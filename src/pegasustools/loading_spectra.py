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


class PegasusSpectralData:
    """Holds all the data loaded when loading a spectra file.

    Stores the time data in a private variable accessible via a getter and stores the spectra data in a numpy array named `data`
    """

    def __init__(self, time: np.float64, size: int = 80000) -> None:
        """Initialize a PegasusSpectralData class with the header data.

        Parameters
        ----------
        time : np.float64
            The simulation time in the file.
        size : int
            The size of the spectra, by default 80000
        """
        # Header variable
        self.__time: np.float64 = time

        # The np.array that actually stores the data
        self.data: np.typing.NDArray[np.float64] = np.empty(size)

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


def _load_spectra(file_path: Path) -> PegasusSpectralData:
    # Open the file
    with file_path.open(mode="rb") as spec_file:
        # Read the header
        nproc = 5376
        final = np.zeros((nproc, 80000))

        spec_file.readline()
        for ii in range(nproc):
            struct.unpack("@d", spec_file.read(8))[0]
            struct.unpack("@d", spec_file.read(8))[0]
            struct.unpack("@d", spec_file.read(8))[0]
            struct.unpack("@d", spec_file.read(8))[0]
            struct.unpack("@d", spec_file.read(8))[0]
            struct.unpack("@d", spec_file.read(8))[0]
            for jj in range(80000):
                final[ii, jj] = struct.unpack("@d", spec_file.read(8))[0]

    return final

    # Load the data

    # Rearrange the data into the correct shape
