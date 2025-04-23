"""Provides the utilities required to deal with particle track data.

This module provides:
- PegasusTrack: A class for holding track data from particles
"""

from pathlib import Path

import h5py
import numpy as np


class PegasusTrack:
    """Holds all the data for a particle track.

    It stores all the header data into private variables that are accessible via getters
    and stores the data in a numpy structured array named 'data' with column names
    identical to the column names in the file.
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
        if extension == [".track", ".dat"]:
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
            msg = f"The file at {file_path} is not a Pegasus++ tracked particle file."
            raise RuntimeError(msg)

    def __load_from_hdf5(
        self, file_path: Path, block_id: int, particle_id: int
    ) -> None:
        pass

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


def collate_tracks_from_ascii(source_directory: Path, destination_path: Path) -> None:
    # Verify the source path
    if not source_directory.is_dir():
        msg = f"{source_directory} is not a directory or does not exist."
        raise ValueError(msg)

    # Get the list of files
    track_dat_files = tuple(source_directory.glob("*.track.dat"))

    # ===== Compute some meta data to save to the HDF5 file =====

    # Get a list of the fields
    with track_dat_files[0].open("r") as track_file:
        # Read the header
        _ = track_file.readline()
        column_headers = track_file.readline().split()

        # Parse column names
        column_headers = column_headers[1:]  # cut out the comment character
        column_names = [raw_name.split("=")[-1] for raw_name in column_headers]
        column_names.append("mu")  # The magnetic moment, computed before saving to disk

    # Determine the number of particles and number of meshblocks
    names = [file_path.stem for file_path in track_dat_files]
    particle_block_ids = np.array([name.split(".")[1:3] for name in names]).astype(int)
    num_blocks = particle_block_ids[:, 1].max()
    num_particles = particle_block_ids[:, 0].max()

    # Create the HDF5 file and add metadata
    with h5py.File(destination_path, "w-") as collated_file:
        # Add name of the run to the attributes
        collated_file.attrs["name"] = track_dat_files[0].stem.split(".")[0]

        # Add a list of the fields to the attributes
        collated_file.attrs["fields"] = column_names

        # Add the number of blocks and particles
        collated_file.attrs["num_meshblocks"] = num_blocks
        collated_file.attrs["num_particles"] = num_particles

    # Loop over list of files in parallel and process then write them to an HDF5 file.
    # Making sure to lock the HDF5 file to avoid parallel writes.
