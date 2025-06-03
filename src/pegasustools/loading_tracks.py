"""Provides the utilities required to deal with particle track data.

This module provides:
- PegasusTrack: A class for holding track data from particles
"""

import concurrent.futures
import itertools
import logging
import multiprocessing
from pathlib import Path
from timeit import default_timer
from typing import Any

import h5py
import numpy as np
import polars as pl
from numpy.lib import recfunctions as np_rfn

logger = logging.getLogger("pt.logger")


class PegasusTrack:
    """Holds all the data for a particle track.

    It stores all the header data into private variables that are accessible via getters
    and stores the data in a numpy structured array named 'data' with column names
    identical to the column names in the file. When loading an HDF5 file the `data`
    member is instead an HDF5 dataset, it can be indexed the same as the numpy
    structured array.
    """

    def __init__(
        self,
        file_path: Path,
        block_id: int = -1,
        particle_id: int = -1,
    ) -> None:
        """Initialize a PegasusTrack object.

        PegasusTrack objects can be initialized in one of two ways:

        1. From the raw .track.dat file at file_path
        2. From the collated track data in the HDF5 file at file_path. It will get the
           dataset with particle_id and block_id

        Parameters
        ----------
        file_path : Path
            The path to the file with the track data
        block_id : int, optional
            The block ID for the particle track to load. Required when loading a track
            from a collated HDF5 file, ignored otherwise.
        particle_id : int, optional
            The particle ID for the particle track to load. Required when loading a
            track from a collated HDF5 file, ignored otherwise.

        Raises
        ------
        ValueError
            Raised if block_id and particle_id are not positive ints when loading from a
            collated HDF5 file.
        RuntimeError
            Raised if the file extension does not match either `.hdf5` or `.track.dat`.
        """
        # Create the member variables
        self.__block_id: int
        self.__particle_id: int
        self.data: np.typing.ArrayLike

        # Check the extension and dispatch to the proper loading function
        extension = file_path.suffixes
        if extension[-2:] == [".track", ".dat"]:
            self.__load_from_ascii(file_path)
        elif extension == [".hdf5"]:
            if block_id < 0 or particle_id < 0:
                msg = (
                    "block_id and particle_id are required when loading a dataset from "
                    "a collated HDF5 file and they both must be positive ints."
                )
                raise ValueError(msg)
            self.__load_from_hdf5(file_path, block_id, particle_id)
        else:
            msg = (
                f"The file at {file_path} with extension {extension} is not a "
                "Pegasus++ tracked particle file."
            )
            raise RuntimeError(msg)

    def __load_from_hdf5(
        self, file_path: Path, block_id: int, particle_id: int
    ) -> None:
        with h5py.File(file_path, "r") as track_file:
            dataset = track_file[f"{block_id}-{particle_id}"]
            self.__block_id = dataset.attrs["block_id"]
            self.__particle_id = dataset.attrs["particle_id"]
            self.data = dataset[:]

    def __load_from_ascii(self, file_path: Path) -> None:
        """Load the track data from an ascii file at file_path.

        Parameters
        ----------
        file_path : Path
            The path to the .track.dat file

        Raises
        ------
        RuntimeError
            Raised if the file is the wrong format
        """
        with file_path.open() as track_file:
            # Read the header
            header = track_file.readline().split()
            column_headers = track_file.readline().split()

            # Verify the headers
            fiducial_header_start = [
                "#",
                "Pegasus++",
                "track",
                "data",
                "for",
                "particle",
                "with",
            ]
            if header[:7] != fiducial_header_start:
                msg = f"The file at {file_path} is not a Pegasus++ .track.dat file."
                raise RuntimeError(msg)

            # Parse the header
            self.__particle_id = int(header[-3].split("=")[-1])
            self.__block_id = int(header[-1].split("=")[-1])

            # Parse column names
            column_headers = column_headers[1:]  # cut out the comment character
            column_names = [raw_name.split("=")[-1] for raw_name in column_headers]

            # Load the file
            data_type = [(name, np.float32) for name in column_names]
            self.data = np.loadtxt(track_file, dtype=data_type)

        # ===== Look for restarts and remove the duplicated data via masking =====
        # Find the indices of the restart times. The +1 shifts from the end of the
        # old data to the beginning of the restart which is what we actually want
        restart_indices = (
            np.flatnonzero(self.data["time"][1:] <= self.data["time"][:-1]) + 1
        )

        # Generate the mask
        mask = np.ones(self.data.shape[0], dtype="bool")
        for end_idx in restart_indices:
            start_idx, _ = np.flatnonzero(
                self.data["time"] == self.data["time"][end_idx]
            )
            mask[start_idx:end_idx] = False

        # Mask out the duplicated data
        self.data = self.data[mask]

    def compute_magnetic_moment(self) -> None:
        """Compute the magnetic moment & add it to `data` if it's not already there."""
        # skip if it's already been computed
        if "mu" in self.data.dtype.names:
            return

        # specific velocities
        specific_velocities = np_rfn.structured_to_unstructured(
            self.data[["v1", "v2", "v3"]]
        ) - np_rfn.structured_to_unstructured(self.data[["U1", "U2", "U3"]])

        # Magnetic fields
        magnetic_fields = np_rfn.structured_to_unstructured(
            self.data[["B1", "B2", "B3"]]
        )

        velocities_sqr = (specific_velocities**2).sum(axis=1)
        magnetic_magnitude = np.sqrt((magnetic_fields**2).sum(axis=1))

        # specific field-parallel velocity
        velocity_prl = (specific_velocities * magnetic_fields).sum(
            axis=1
        ) / magnetic_magnitude

        # mu invariant
        mu = 0.5 * (velocities_sqr - velocity_prl**2) / magnetic_magnitude

        self.data = np_rfn.append_fields(self.data, "mu", mu)

    @property
    def particle_id(self) -> int:
        """Get the particle ID.

        Returns
        -------
        int
            The particle ID within the meshblock.
        """
        return self.__particle_id

    @property
    def block_id(self) -> int:
        """Get the meshblock ID.

        Returns
        -------
        int
            The meshblock ID .
        """
        return self.__block_id


def collate_tracks_from_ascii(
    source_directory: Path, destination_path: Path | None = None, max_processes: int = 6
) -> None:
    """Collate the .track.dat files in a directory into one file.

    Parameters
    ----------
    source_directory : Path
        The path to the directory with the .track.dat files
    destination_path : Path, optional
        The path with filename where the HDF5 file should be created. Defaults to
        putting the HDF5 file in the same directory as the track.dat files with the name
        `<problem-name>_collated_tracks.hdf5`
    max_processes : int, optional
        The number of processes to use. The default of 6 was chosen empirically since
        that was the maximum number of processes that can be used before the parallel
        speedup stops improving significantly on Della.

    Raises
    ------
    ValueError
        Raised if source_directory does not exist or isn't a directory.
    """
    # 12 the the maximum number of processes that can be used before the parallel
    # speedup stops improving

    # Verify the source path
    if not source_directory.is_dir():
        msg = f"{source_directory} is not a directory or does not exist."
        raise ValueError(msg)

    # Get the list of files
    track_dat_paths = tuple(source_directory.glob("*.track.dat"))

    # Set the destination file name if it isn't provided
    if destination_path is None:
        problem_name = track_dat_paths[0].name.split(".")[0]
        name = f"{problem_name}_collated_tracks.hdf5"
        destination_path = source_directory / name

    # ===== Compute some meta data to save to the HDF5 file =====

    # Get a list of the fields
    with track_dat_paths[0].open("r") as track_file:
        # Read the header
        _ = track_file.readline()
        column_headers = track_file.readline().split()

        # Parse column names
        column_headers = column_headers[1:]  # cut out the comment character
        column_names = [raw_name.split("=")[-1] for raw_name in column_headers]
        column_names.append("mu")  # The magnetic moment, computed before saving to disk

    # Determine the number of particles and number of meshblocks
    names = [file_path.stem for file_path in track_dat_paths]
    particle_block_ids = np.array([name.split(".")[1:3] for name in names]).astype(int)
    num_blocks = particle_block_ids[:, 1].max()
    num_particles = particle_block_ids[:, 0].max()

    # Create the HDF5 file and add metadata
    with h5py.File(destination_path, "w-") as collated_file:
        # Add name of the run to the attributes
        collated_file.attrs["name"] = track_dat_paths[0].stem.split(".")[0]

        # Add a list of the fields to the attributes
        collated_file.attrs["fields"] = column_names

        # Add the number of blocks and particles
        collated_file.attrs["num_meshblocks"] = num_blocks
        collated_file.attrs["num_particles"] = num_particles

    # Loop over list of files in parallel and process then write them to an HDF5 file.
    # Making sure to lock the HDF5 file to avoid parallel writes.
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_processes) as executor:
        lock = multiprocessing.Manager().Lock()
        _ = [
            executor.submit(
                _parallel_ascii_collater, track_path, destination_path, lock
            )
            for track_path in track_dat_paths
        ]


def _parallel_ascii_collater(
    track_path: Path,
    destination_path: Path,
    lock: Any,  # noqa: ANN401
) -> None:
    # Load the file into memory
    loaded_track = PegasusTrack(track_path)

    # Add the magnetic moment to the data
    loaded_track.compute_magnetic_moment()

    # Make the dataset name
    dataset_name = f"{loaded_track.block_id}-{loaded_track.particle_id}"

    # Save the data to the HDF5 file
    with lock, h5py.File(destination_path, "r+") as collated_file:
        if dataset_name not in collated_file:
            dataset = collated_file.create_dataset(dataset_name, data=loaded_track.data)
            dataset.attrs["block_id"] = loaded_track.block_id
            dataset.attrs["particle_id"] = loaded_track.particle_id


def _binary_get_column_names(
    num_columns: int,
) -> tuple[tuple[str, ...], tuple[Any, ...]]:
    # Determine which columns are in this dataset
    column_names = [
        "particle_id",
        "block_id",
        "species",
        "time",
        "x1",
        "x2",
        "x3",
        "v1",
        "v2",
        "v3",
        "B1",
        "B2",
        "B3",
        "E1",
        "E2",
        "E3",
        "U1",
        "U2",
        "U3",
        "dens",
        "forcing1",
        "forcing2",
        "forcing3",
    ]

    match num_columns:
        case 18:  # 1D no forcing
            column_names.remove("x2")
            column_names.remove("x3")
            column_names.remove("forcing1")
            column_names.remove("forcing2")
            column_names.remove("forcing3")
        case 19:  # 2D no forcing
            column_names.remove("x3")
            column_names.remove("forcing1")
            column_names.remove("forcing2")
            column_names.remove("forcing3")
        case 20:  # 3D no forcing
            column_names.remove("forcing1")
            column_names.remove("forcing2")
            column_names.remove("forcing3")
        case 21:  # 1D with forcing
            column_names.remove("x2")
            column_names.remove("x3")
        case 22:  # 2D with forcing
            column_names.remove("x3")
        case 23:  # 3D with forcing
            pass

    column_types = []
    for name in column_names:
        if name in ("particle_id", "block_id", "species"):
            column_types.append(pl.datatypes.Int64)
        else:
            column_types.append(pl.datatypes.Float64)

    return tuple(column_names), tuple(column_types)


def _compute_magnetic_moment(
    data: np.typing.ArrayLike,
    column_names: tuple[str, ...],
    column_types: tuple[Any, ...],
) -> tuple[np.typing.ArrayLike, tuple[str, ...], tuple[Any, ...]]:
    v_start = column_names.index("v1")
    b_start = column_names.index("B1")
    u_start = column_names.index("U1")

    # specific velocities
    specific_velocities = (
        data[:, v_start : v_start + 3] - data[:, u_start : u_start + 3]
    )

    # Magnetic fields
    magnetic_fields = data[:, b_start : b_start + 3]

    velocities_sqr = (specific_velocities**2).sum(axis=1)
    magnetic_magnitude = np.sqrt((magnetic_fields**2).sum(axis=1))

    # specific field-parallel velocity
    velocity_prl = (specific_velocities * magnetic_fields).sum(
        axis=1
    ) / magnetic_magnitude

    # mu invariant
    mu = 0.5 * (velocities_sqr - velocity_prl**2) / magnetic_magnitude

    # append mu to data
    mu = np.expand_dims(mu, axis=1)
    data = np.hstack((data, mu))

    # Expand the column nameds and schema to include mu
    column_names = (*column_names, "mu")
    column_types = (*column_types, pl.datatypes.Float64)

    return data, column_names, column_types


def _binary_track_reader(input_file_path: Path, parquet_path: Path) -> pl.DataFrame:
    # Open the file
    with input_file_path.open(mode="rb") as spec_file:
        # skip the header row
        _ = spec_file.readline()

        # Load the entire remaining file
        data = np.fromfile(spec_file, dtype=np.float64)

    # Determine the size of each row
    abs_allowed_err = 5.0e-13
    int_to_float_offset = 0.001
    for i in range(17, 25):
        diff1 = np.abs((data[i] - np.floor(data[i])) - int_to_float_offset)
        diff2 = np.abs((data[i + 1] - np.floor(data[i + 1])) - int_to_float_offset)

        if diff1 < abs_allowed_err and diff2 < abs_allowed_err:
            num_columns = i
            break

    # Reshape to the proper shape
    data = data.reshape((data.shape[0] // num_columns, num_columns))

    # Get the list of column names
    column_names, column_types = _binary_get_column_names(num_columns)

    # Compute mu
    data, column_names, column_types = _compute_magnetic_moment(
        data, column_names, column_types
    )

    # Convert to dataframe
    column_schema = tuple(zip(column_names, column_types, strict=True))
    output_df = pl.from_numpy(data, schema=column_schema)

    # Get mins and maxes
    mins = output_df.select(pl.col("species")).min()
    maxes = output_df.select(pl.col("particle_id"), pl.col("species")).max()

    # Write to disk
    output_df.write_parquet(parquet_path)

    return pl.DataFrame(
        {
            "species_mins": mins["species"].item(),
            "species_maxes": maxes["species"].item(),
            "particle_id_maxes": maxes["particle_id"].item(),
        }
    )


def _compute_global_ids(
    parquet_path: Path, species_min: int, species_max: int, particles_max: int
) -> pl.DataFrame:
    # Load the dataframe
    logger.debug("Starting %s", parquet_path)
    output_df = pl.read_parquet(parquet_path)

    # Compute new IDs
    n_species = species_max - species_min + 1
    n_particles = particles_max + 1
    output_df = output_df.with_columns(
        particle_id=(pl.col("species") - species_min)
        + (pl.col("particle_id") * n_species)
        + (pl.col("block_id") * n_species * n_particles)
    )

    # Sort
    output_df = output_df.sort(["particle_id", "time"])

    # Get the unique IDs
    unique_ids = output_df["particle_id"].unique()

    # Write to disk
    output_df.write_parquet(parquet_path)

    logger.debug("finished with %s", parquet_path)

    return unique_ids


def _collect_particles_and_compute_delta_mu(
    parquet_paths: tuple[Path], chunk: tuple[int, int]
) -> None:
    # Filter to find all the particles in the chunk
    selections = [
        pl.scan_parquet(pq_path).filter(
            pl.col("particle_id").is_between(chunk[0], chunk[1])
        )
        for pq_path in parquet_paths
    ]

    # Collect and sort the particle data
    full_set = (
        pl.concat(selections).collect(engine="streaming").sort(["particle_id", "time"])
    )

    # Compute delta mu
    full_set = full_set.with_columns(
        delta_mu_abs=pl.when(pl.col("particle_id") == pl.col("particle_id").shift())
        .then((pl.col("mu") - pl.col("mu").shift()).abs())
        .otherwise(None)
    )

    # Write the results
    output_name = (
        "_".join(parquet_paths[0].stem.split("_")[:-2])
    ) + f"_particles_{chunk[0]}_{chunk[1]}.parquet"
    full_set.write_parquet(parquet_paths[0].parent / output_name)


def collate_tracks_from_binary(
    num_processes: int, source_dir: Path, destination_dir: Path
) -> None:
    """Collate the .track_mpiio_optimized files in a directory into ordered files.

    Parameters
    ----------
    num_processes : int
        The number of processes to use.
    source_dir : Path
        The path to the directory with the .track_mpiio_optimized files
    destination_dir : Path
        The path with filename where the parquet files should be created.
    """
    logger.info("Gathering list of .track_mpiio_optimized files.")
    # Get list of binary files
    files_to_read = sorted(source_dir.glob("*.track_mpiio_optimized"))

    # Make a tuple of the parquet files that will be generated
    parquet_paths = tuple(
        destination_dir / ("_".join(f.stem.split(".")) + "_temp.parquet")
        for f in files_to_read
    )

    # Spawning new processes instead of forking is required for polars
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=num_processes, mp_context=multiprocessing.get_context("spawn")
    ) as executor:
        logger.info("ProcessPoolExecutor launched")
        # Convert the binary files to parquet and get the mins & maxes for IDs
        start = default_timer()
        extrema = pl.concat(
            executor.map(
                _binary_track_reader,
                files_to_read,
                parquet_paths,
            )
        )
        logger.info(
            "Initial Conversion complete. Elapsed time: %.2fs", default_timer() - start
        )

        # Compute the min & max IDs
        mins = extrema.select(pl.col("species_mins")).min()
        maxes = extrema.select(
            pl.col("species_maxes"), pl.col("particle_id_maxes")
        ).max()
        logger.info("Finished with determining min & max IDs")

        # Compute the new global IDs and get a list of all unique IDs.
        start = default_timer()
        unique_ids = (
            pl.concat(
                executor.map(
                    _compute_global_ids,
                    parquet_paths,
                    itertools.repeat(mins["species_mins"].item()),
                    itertools.repeat(maxes["species_maxes"].item()),
                    itertools.repeat(maxes["particle_id_maxes"].item()),
                )
            )
            .unique()
            .sort()
        )
        logger.info(
            "Computing global IDs and sorting complete. Elapsed time: %.2fs",
            default_timer() - start,
        )

        # Determine work group ranges
        num_chunks = len(parquet_paths)
        start = 0
        step = int(np.ceil(len(unique_ids) / num_chunks))

        ranges = []
        while True:
            stop = start + step
            if stop < len(unique_ids):
                ranges.append((unique_ids[start], unique_ids[stop]))
                start = stop + 1
            else:
                ranges.append((unique_ids[start], unique_ids[-1]))
                break
        logger.info("Finished with determining work group ranges")

        # Collect data for each block of particles into a single parquet file
        start = default_timer()
        _ = executor.map(
            _collect_particles_and_compute_delta_mu,
            itertools.repeat(parquet_paths),
            ranges,
        )

    logger.info(
        "Collecting particles into their own files complete. Elapsed time: %.2fs",
        default_timer() - start,
    )

    # Clean up the temporary files
    start = default_timer()
    for path in parquet_paths:
        path.unlink()
    logger.info(
        "Deleting temporary files complete. Elapsed time: %.2fs",
        default_timer() - start,
    )
