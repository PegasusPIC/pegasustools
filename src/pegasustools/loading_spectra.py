"""Provides the utilities required to load output files from Pegasus++.

This module provides:
- PegasusSpectralData: A class for holding the data loaded from a spectra file
- _load_spectra: A function for loading spectra files
"""

import struct
from pathlib import Path
from typing import BinaryIO

import numpy as np


def og_spectra_reader(file_path: Path) -> np.typing.NDArray[np.float64]:
    """Original reading function. DELETE ME."""
    final = np.zeros(80000)
    nproc = 5376

    with file_path.open("rb") as f:
        f.readline()
        for ii in range(nproc):  # noqa: B007
            struct.unpack("@d", f.read(8))[0]
            struct.unpack("@d", f.read(8))[0]
            struct.unpack("@d", f.read(8))[0]
            struct.unpack("@d", f.read(8))[0]
            struct.unpack("@d", f.read(8))[0]
            struct.unpack("@d", f.read(8))[0]
            for jj in range(80000):
                final[jj] = final[jj] + struct.unpack("@d", f.read(8))[0]

    return final


class PegasusSpectralData:
    """Holds all the data loaded when loading a spectra file.

    Stores the time data in a private variable accessible via a getter and stores the spectra data in a numpy array named `spectra`
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
        """Get the simulation time of the NBF file.

        Returns
        -------
        np.float64
            The time in the NBF file
        """
        return self.__time


def _load_nbf_header(nbf_file: BinaryIO) -> PegasusSpectralData:
    # Load the header lines and verify it's an NBF file
    bad_file_message = f"{nbf_file.name} is not a Pegasus++ NBF file."
    try:
        header_size = 9  # The number of lines in the header
        header_list = [next(nbf_file).decode("ascii") for _ in range(header_size)]
    except StopIteration as exception:
        raise OSError(bad_file_message) from exception

    # Verify that this is a Pegasus++ NBF file by examining the first line
    first_line = "Pegasus++ binary output at time = "
    if header_list[0][0:34] != first_line:
        raise OSError(bad_file_message)

    # Now let's parse the header

    # Line 0: The time of the output
    time = np.float64(header_list[0].split()[-1])

    # Build the PegasusNBFData object to return the header info
    return PegasusSpectralData(time=time)


def _load_nbf_meshblock(
    nbf_file: BinaryIO,
    starting_offset: int,
    meshblock_header_size: int,
    nbf_data: PegasusSpectralData,
) -> None:
    nbf_file.seek(starting_offset)
    # Load the meshblock header, discarding values we don't need
    (
        x1_block_coord,
        x2_block_coord,
        x3_block_coord,
        x1_block_size,
        _,
        _,
        x2_block_size,
        _,
        _,
        x3_block_size,
        _,
        _,
    ) = struct.unpack("@4i2fi2fi2f", nbf_file.read(meshblock_header_size))

    # # Compute the indices to write to
    # i_start = x1_block_coord * nbf_data.meshblock_params["nx1"]
    # i_end = i_start + x1_block_size
    # j_start = x2_block_coord * nbf_data.meshblock_params["nx2"]
    # j_end = j_start + x2_block_size
    # k_start = x3_block_coord * nbf_data.meshblock_params["nx3"]
    # k_end = k_start + x3_block_size

    # block_size = x1_block_size * x2_block_size * x3_block_size

    # data = np.fromfile(
    #     nbf_file, dtype=np.float32, count=block_size * nbf_data.num_variables, offset=0
    # )
    # data = data.reshape(
    #     nbf_data.num_variables, x3_block_size, x2_block_size, x1_block_size
    # )

    # for nv in range(nbf_data.num_variables):
    #     field_key = nbf_data.list_of_variables[nv]

    #     nbf_data.data[field_key][k_start:k_end, j_start:j_end, i_start:i_end] = data[
    #         nv, :, :, :
    #     ]


def _load_nbf(filepath: Path) -> PegasusSpectralData:
    # Open the file
    with filepath.open(mode="rb") as nbf_file:
        # Read the header
        nbf_data = _load_nbf_header(nbf_file)

        # # loop over all meshblocks and read all variables
        # for meshblock_id in range(nbf_data.num_meshblocks):
        #     _load_nbf_meshblock(
        #         nbf_file,
        #         meshblock_id * meshblock_size + header_size,
        #         meshblock_header_size,
        #         nbf_data,
        #     )

    # Swap axis so the data is formatted as (Nx1, Nx2, Nx3) and remove dimensions of length 1
    # Moving this into _load_nbf_meshblock causes a 30% slowdown
    for key in nbf_data.data:
        nbf_data.data[key] = np.swapaxes(nbf_data.data[key], 0, 2)
        nbf_data.data[key] = np.squeeze(nbf_data.data[key])

    return nbf_data
