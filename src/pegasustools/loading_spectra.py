"""Provides the utilities required to load output files from Pegasus++.

This module provides:
- PegasusSpectralData: A class for holding the data loaded from a spectra file
- _load_spectra: A function for loading spectra files
"""

import struct
from pathlib import Path

import numpy as np


def og_spectra_reader(file_path: Path) -> np.typing.NDArray[np.float64]:
    """Original reading function. DELETE ME."""
    nproc = 5376
    final = np.zeros((nproc, 80000))

    with file_path.open("rb") as f:
        f.readline()
        for ii in range(nproc):
            struct.unpack("@d", f.read(8))[0]
            struct.unpack("@d", f.read(8))[0]
            struct.unpack("@d", f.read(8))[0]
            struct.unpack("@d", f.read(8))[0]
            struct.unpack("@d", f.read(8))[0]
            struct.unpack("@d", f.read(8))[0]
            for jj in range(80000):
                final[ii, jj] = struct.unpack("@d", f.read(8))[0]

    return final


def og_spectra_reader_with_sum(file_path: Path) -> np.typing.NDArray[np.float64]:
    """Original reading function. DELETE ME."""
    nproc = 5376
    final = np.zeros(80000)

    with file_path.open("rb") as f:
        f.readline()
        for _ii in range(nproc):
            struct.unpack("@d", f.read(8))[0]
            struct.unpack("@d", f.read(8))[0]
            struct.unpack("@d", f.read(8))[0]
            struct.unpack("@d", f.read(8))[0]
            struct.unpack("@d", f.read(8))[0]
            struct.unpack("@d", f.read(8))[0]
            for jj in range(80000):
                final[jj] += struct.unpack("@d", f.read(8))[0]

    return final


class PegasusSpectralData:
    """Holds all the data loaded when loading a spectra file.

    Stores the time data in a private variable accessible via a getter and stores the
    spectra data in a numpy array named `data`
    """

    def __init__(
        self, file_path: Path, num_parallel: int = 400, num_perpendicular: int = 200
    ) -> None:
        """Initialize a PegasusSpectralData class with the header data.

        Parameters
        ----------
        file_path : Path
            The file path to the file to load
        num_parallel : int, optional
            The value of n_prl used in the peginput file, by default 400
        num_perpendicular : int, optional
            The value of n_prp used in the peginput file, by default 200

        Raises
        ------
        ValueError
            Raised if the file does not have the right number of elements for the
            provided num_parallel and num_perpendicular
        """
        # Open the file
        with file_path.open(mode="rb") as spec_file:
            # Load header variable
            header = spec_file.readline().decode("ascii")
            self.__time: np.float64 = np.float64(header.split()[-1])

            # Load the entire remaining file
            self.data = np.fromfile(spec_file, dtype=np.float64)

            # Get the info to reshape the array
            block_header_size = 6  # The header of each block is 6 elements
            num_row = num_parallel * num_perpendicular + block_header_size
            num_col = self.data.size // num_row

            # Check that the file is actually the right size for the number of elements
            # per spectra. Note that this check isn't perfect, it just verifies that the
            # file can be exactly divided by the number of elements provided.
            if self.data.size % num_row != 0:
                err_msg = (
                    f"The file {file_path} does not have the right number of "
                    f"elements for the values of {num_parallel = } and "
                    f"{num_perpendicular = } provided."
                )
                raise ValueError(err_msg)

            # Rearrange the data into the correct shape and trim off the header elements
            # in each block
            self.data = self.data.reshape((num_col, num_row))
            self.data = self.data[:, 6:]

    # Define getters for header variables
    @property
    def time(self) -> np.float64:
        """Get the simulation time of the spectra file.

        Returns
        -------
        np.float64
            The time in the spectra file
        """
        return self.__time

    def sum_over_meshblocks(self) -> np.typing.NDArray[np.float64]:
        """Sum over all meshblocks in the spectraself.

        This is equivalent to `np.sum(self.data, axis=0)`.

        Returns
        -------
        np.typing.NDArray[np.float64]
            The summed spectra
        """
        summed_spectra: np.typing.NDArray[np.float64] = np.sum(self.data, axis=0)
        return summed_spectra
