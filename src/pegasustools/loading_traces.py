"""Provides the utilities required to deal with trace data."""

# pylint: disable=duplicate-code
import concurrent.futures
import multiprocessing
from pathlib import Path
from timeit import default_timer

import numpy as np
import polars as pl

from .loading_tracks import _binary_get_column_names_included_header
from .pt_logging import setup_pt_logger


def _trace_reader(input_file_path: Path, parquet_path: Path) -> pl.DataFrame:
    """Convert binary trace file to parquet file.

    Parameters
    ----------
    input_file_path : Path
        The path to the `.trace_mpiio_optimized` file.
    parquet_path : Path
        The directory to write the parquet file to.

    Returns
    -------
    pl.DataFrame
        All the unique trace IDs
    """
    logger = setup_pt_logger()
    logger.debug("Starting with file %s", input_file_path)

    # Open the file
    with input_file_path.open(mode="rb") as trace_file:
        # first read the header
        _ = trace_file.readline()
        line_2 = trace_file.readline().decode("ascii")
        line_3 = trace_file.readline().decode("ascii")

        # Load the binary part of the file
        data = np.fromfile(trace_file, dtype=np.float64)

    # Build the schema
    num_columns, column_schema = _binary_get_column_names_included_header(
        line_2, line_3
    )

    # Reshape to the proper shape
    num_rows = data.shape[0] // num_columns
    data = data.reshape((num_rows, num_columns))

    # Convert to dataframe
    output_df = pl.from_numpy(data, schema=column_schema)

    # Write to disk
    output_df.write_parquet(parquet_path)

    logger.debug("Finished with file %s", input_file_path)

    return output_df["block_id"].unique()


def _collect_traces(parquet_paths: tuple[Path, ...], chunk: tuple[int, int]) -> None:
    """Gather all data points for traces into single files.

    This function takes a list of parquet files and a range of trace IDs then finds
    all the data for every trace in that range and collects it all into a single
    file. It then sorts that data according to trace ID and time. Results are written to
    new parquet files.

    Parameters
    ----------
    parquet_paths : tuple[Path, ...]
        The paths to the parquet files
    chunk : tuple[int, int]
        The IDs of the traces to collect. The first element is the low limit and the
        second element is the upper limit, both inclusive.
    """
    logger = setup_pt_logger()
    logger.debug("Starting with trace range %i-%i", chunk[0], chunk[1])

    # Filter to find all the traces in the chunk
    selected_particles = (
        pl.scan_parquet(parquet_paths)
        .filter(pl.col("block_id").is_between(chunk[0], chunk[1]))
        .collect(engine="streaming")
    )

    # Sort the particle data
    selected_particles = selected_particles.sort(["block_id", "time"])

    # Write the results
    output_name = (
        "_".join(parquet_paths[0].stem.split("_")[:-2])
    ) + f"_traces_{chunk[0]}_{chunk[1]}.parquet"
    output_path = parquet_paths[0].parent / output_name
    selected_particles.write_parquet(output_path)

    logger.debug("Finished with trace range %i-%i", chunk[0], chunk[1])


def collate_traces(
    num_processes: int,
    source_dir: Path,
    destination_dir: Path,
) -> None:
    """Collate the .trace_mpiio_optimized files in a directory into ordered files.

    Parameters
    ----------
    num_processes : int
        The number of processes to use.
    source_dir : Path
        The path to the directory with the .trace_mpiio_optimized files
    destination_dir : Path
        The path with filename where the parquet files should be created. It will be
        created if it doesn't exist.
    """
    # Setup logging
    logger = setup_pt_logger()

    # Get list of binary files
    logger.info("Gathering list of .trace_mpiio_optimized files.")
    files_to_read = sorted(source_dir.glob("*.trace_mpiio_optimized"))

    # Create destination directory if it doesn't already exist
    destination_dir.mkdir(parents=True, exist_ok=True)

    # Make a tuple of the parquet files that will be generated
    parquet_paths = tuple(
        destination_dir / ("_".join(f.stem.split(".")) + "_temp.parquet")
        for f in files_to_read
    )

    # Spawning new processes instead of forking is required for polars
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=num_processes, mp_context=multiprocessing.get_context("spawn")
    ) as executor:
        logger.info(
            "ProcessPoolExecutor launched with %i processes. "
            "Using %i Polars threads each.",
            num_processes,
            pl.thread_pool_size(),
        )
        # Convert the binary files to parquet
        start = default_timer()
        futures = [
            executor.submit(
                _trace_reader,
                files_to_read[i],
                parquet_paths[i],
            )
            for i in range(len(files_to_read))
        ]

        # Get a list of all the unique trace IDs
        unique_ids = pl.concat([future.result() for future in futures]).unique().sort()
        logger.info(
            "Initial Conversion complete. Elapsed time: %.2fs",
            default_timer() - start,
        )

        # Determine work group ranges
        num_chunks = len(parquet_paths)
        start_idx = 0
        step = int(np.ceil(len(unique_ids) / num_chunks))

        ranges = []
        while True:
            stop = start_idx + step
            if stop < len(unique_ids):
                ranges.append((unique_ids[start_idx], unique_ids[stop]))
                start_idx = stop + 1
            else:
                ranges.append((unique_ids[start_idx], unique_ids[-1]))
                break
        logger.info("Finished with determining work group ranges")

        # Collect data for each block of particles into a single parquet file
        collect_start = default_timer()
        futures = [executor.submit(_collect_traces, parquet_paths, r) for r in ranges]
        # Check for errors and collect results
        _ = [future.result() for future in futures]
        logger.info(
            "Collecting particles into their own files complete. Elapsed time: %.2fs",
            default_timer() - collect_start,
        )

    # Clean up the temporary files
    delete_temps_start = default_timer()
    for path in parquet_paths:
        path.unlink()
    logger.info(
        "Deleting temporary files complete. Elapsed time: %.2fs",
        default_timer() - delete_temps_start,
    )

    logger.info(
        "Finished sorting and collecting particle data. Total time:: %.2fs",
        default_timer() - start,
    )
