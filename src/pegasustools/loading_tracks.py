"""Provides the utilities required to deal with particle track data.

This module provides:
- TODO
"""

from pathlib import Path

import numpy as np


class PegasusTrackASCII:
    """Holds all the data loaded when loading an ASCII track file (.track.dat files).

    It stores all the header data into private variables that are accessible via getters
    and stores the data in a numpy structured array named 'data' with column names
    identical to the column names in the .track.dat file.
    """

    def __init__(self, file_path: Path) -> None:
        """Initialize a PegasusTrackASCII object from the .track.dat file at file_path.

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
                msg = (
                    f"The file at {file_path} does not appear to be a Pegasus++ "
                    "Tracked Particle file"
                )
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
