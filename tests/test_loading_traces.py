"""Tests for the contents of loading_traces.py."""

from pathlib import Path

import numpy as np
import polars as pl
import polars.testing

import pegasustools as pt


def test_collate_tracks_from_binary() -> None:
    """Test the collate_tracks_from_binary function."""
    # Setup paths
    source_directory = (
        Path(__file__).parent.resolve() / "data" / "test_collate_tracks_from_binary"
    )
    parquet_directory = source_directory / "parquet"
    source_directory.mkdir(exist_ok=True)
    parquet_directory.mkdir(exist_ok=True)

    # Generate test data
    num_files = 3
    fiducial_data = pl.concat(
        [
            generate_random_trace_binary(
                source_directory / f"test_file_{i}.trace_mpiio_optimized", seed=42 + i
            )
            for i in range(num_files)
        ]
    )

    # Sort Test Data
    fiducial_data = fiducial_data.sort(["block_id", "time"])

    # Run the code to test
    num_procs = min(num_files, 12)
    pt.collate_traces(
        num_processes=num_procs,
        source_dir=source_directory,
        destination_dir=parquet_directory,
    )
    test_data = pl.read_parquet(parquet_directory)

    # Verify the results
    polars.testing.assert_frame_equal(test_data, fiducial_data)

    # Cleanup the files created
    [f.unlink() for f in source_directory.glob("*.track_mpiio_optimized")]  # type: ignore[func-returns-value]
    [f.unlink() for f in parquet_directory.glob("*.parquet")]  # type: ignore[func-returns-value]


def generate_random_trace_binary(
    file_path: Path,
    num_meshblocks: int = 96,
    seed: int | None = None,
) -> pl.DataFrame:
    """Generate a .track.dat ASCII file.

    Parameters
    ----------
    file_path : Path
        The path to write the file to
    num_meshblocks : int, optional
        The number of meshblocks, by default 96
    seed : int | None, optional
        The seed for the PRNG, by default None

    Returns
    -------
    pl.DataFrame
        The data written to the binary file.
    """
    # Setup PRNG
    rng = np.random.default_rng(seed)

    # Setup column names
    int_t = pl.datatypes.Int64
    float_t = pl.datatypes.Float64
    column_schema = [
        ("block_id", int_t),
        ("time", float_t),
        ("x1", float_t),
        ("x2", float_t),
        ("x3", float_t),
        ("B1", float_t),
        ("B2", float_t),
        ("B3", float_t),
        ("E1", float_t),
        ("E2", float_t),
        ("E3", float_t),
        ("U1", float_t),
        ("U2", float_t),
        ("U3", float_t),
        ("dens", float_t),
    ]
    num_columns = len(column_schema)

    # Open file
    with file_path.open("wb") as track_file:
        # Write header
        time = rng.uniform(0, 1000, 1)[0]
        header = f"Trace output function at time = {time}\n"
        track_file.write(header.encode("ascii"))

        column_names = "   ".join([column_schema[i][0] for i in range(num_columns)])
        track_file.write(f"Number of variables = {num_columns}\n".encode("ascii"))
        track_file.write(f"Variables:   {column_names}\n".encode("ascii"))

        # Generate random data
        factor = 10
        length = num_meshblocks * factor
        track_data = rng.uniform(-1, 10, num_columns * length)
        track_data = track_data.reshape((length, num_columns))

        # Add the id column
        track_data[:, 0] = (
            np.array(
                [
                    block_id
                    for sublist in [[i] * factor for i in range(num_meshblocks)]
                    for block_id in sublist
                ]
            )
            + 0.001
        )

        # Save the data
        track_data.tofile(track_file)

    # ===== Convert to dataframe =====
    return pl.from_numpy(track_data, schema=column_schema)
