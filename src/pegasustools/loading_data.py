"""Provides the utilities required to load output files from Pegasus++.

This module provides:
- FUNCTION/CLASS NAME: DESCRIPTION
"""

from pathlib import Path
from typing import BinaryIO

import numpy as np


class PegasusNBFData:
    """Holds all the data loaded when loading a NBF file.

    It stores all the header data into private variables that are accessible via getters and stores the data arrays in a dictionary named `data` which is indexed via the variable field names in the NBF fil.
    """

    def __init__(  # noqa: PLR0913
        self,
        time: np.float32,
        num_meshblocks: int,
        num_variables: int,
        list_of_variables: list[str],
        mesh_params: dict[str, np.float32 | int],
        meshblock_params: dict[str, int],
        *,
        big_endian: bool,
    ) -> None:
        """Initialize a PegasusNBFData class with the header data.

        Parameters
        ----------
        time : np.float32
            The simulation time in the file.
        big_endian : bool
            True if the data is big endian, False otherwise.
        num_meshblocks : int
            The number of mesh blocks.
        num_variables : int
            The number of variables/fields in the NBF file.
        list_of_variables : list[str]
            The list of variables in the NBF files.
        mesh_params : dict[str, np.float32  |  int]
            The mesh parameters.
        meshblock_params : dict[str, int]
            The mesh block parameters.
        """
        self.__time = time
        self.__big_endian = big_endian
        self.__num_meshblocks = num_meshblocks
        self.__num_variables = num_variables
        self.__list_of_variables = list_of_variables
        self.__mesh_params = mesh_params
        self.__meshblock_params = meshblock_params

    # Define the header variables
    __time: np.float32
    __big_endian: bool
    __num_meshblocks: int
    __num_variables: int
    __list_of_variables: list[str]
    __mesh_params: dict[str, np.float32 | int]
    __meshblock_params: dict[str, int]

    # Define getters for header variables
    @property
    def time(self) -> np.float32:
        """Get the simulation time of the NBF file.

        Returns
        -------
        np.float32
            The time in the NBF file
        """
        return self.__time

    @property
    def big_endian(self) -> bool:
        """Get the endianness of the NBF file. True if the data is big endian, False otherwise.

        Returns
        -------
        bool
            The endianness of the NBF file. True if the data is big endian, False otherwise.
        """
        return self.__big_endian

    @property
    def num_meshblocks(self) -> int:
        """Get the number of mesh blocks in the NBF file.

        Returns
        -------
        int
            The number of mesh blocks in the NBF file
        """
        return self.__num_meshblocks

    @property
    def num_variables(self) -> int:
        """Get the number of variables in the NBF file.

        Returns
        -------
        int
            The number of variables/fields in the NBF file
        """
        return self.__num_variables

    @property
    def list_of_variables(self) -> list[str]:
        """Get the list of variables in the NBF file.

        Returns
        -------
        list[str]
            The list of variables in the NBF file.
        """
        return self.__list_of_variables

    @property
    def mesh_params(self) -> dict[str, np.float32 | int]:
        """Get the mesh parameters in the NBF file.

        Returns
        -------
        dict[str, np.float32 | int]
            The mesh parameters in the NBF file.
        """
        return self.__mesh_params

    @property
    def meshblock_params(self) -> dict[str, int]:
        """Get the mesh block parameters in the NBF file.

        Returns
        -------
        dict[str, int]
            The mesh block parameters in the NBF file.
        """
        return self.__meshblock_params

    # The dictionary that actually stores the data
    data: dict[str, np.typing.NDArray[np.float32]]


def _load_nbf_header(nbf_file: BinaryIO) -> PegasusNBFData:
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
    time = np.float32(header_list[0].split()[-1])

    # Line 1: Endianness
    big_endian = bool(int(header_list[1].split()[-1]))

    # Line 2: The number of meshblocks
    num_meshblocks = int(header_list[2].split()[-1])

    # Line 3: The number of variables/fields stored in this file
    num_variables = int(header_list[3].split()[-1])

    # Line 4: The list of variables
    list_of_variables = list(header_list[4].split()[1:])

    # Line 5-7: The mesh variables
    # Combine all three lines, split at whitespace, and discard the "Mesh:" part of the line
    combined_lines = (header_list[5] + header_list[6] + header_list[7]).split()[1:]
    # Loop through elements to build a dictionary with values and keys
    mesh_params: dict[str, np.float32 | int] = {}
    for element in combined_lines:
        key, value = element.split("=")
        if key[:2] == "nx":
            mesh_params[key] = int(value)
        elif key[0] == "x":
            mesh_params[key] = np.float32(value)

    # Line 8: Get the meshblock variables
    meshblock_params: dict[str, int] = {}
    for element in header_list[8].split()[1:]:
        key, value = element.split("=")
        meshblock_params[key] = int(value)

    # Build the PegasusNBFData object to return the header info
    return PegasusNBFData(
        time=time,
        big_endian=big_endian,
        num_meshblocks=num_meshblocks,
        num_variables=num_variables,
        list_of_variables=list_of_variables,
        mesh_params=mesh_params,
        meshblock_params=meshblock_params,
    )


def _load_nbf(filepath: Path) -> PegasusNBFData:
    # Open the file
    with filepath.open(mode="rb") as nbf_file:
        # Read the header
        nbf_data = _load_nbf_header(nbf_file)

        # META: Read the binary part of the file
        # Steps:
        # 0. Create target arrays
        # 1. Compute step between meshblocks so all iterations are independent, allowing for parallelization
        # 2. Loop through mesh blocks
        #   3. Load the mesh block header
        #   4. Load the entire data in one go with np.fromfile
        #   5. Reshape data
        #   6. Copy data into target arrays
        # - Try loading each variable one at a time
        # - Can I skip reading each meshblock header??? Probably not
        # - If execution time isn't down to <100ms then try asyncio https://stackoverflow.com/a/59385935
        return nbf_data  # noqa: RET504
