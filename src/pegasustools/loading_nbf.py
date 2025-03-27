"""Provides the utilities required to load output files from Pegasus++.

This module provides:
- PegasusNBFData: A class for holding the data loaded from a NBF file
- _load_nbf: A function for loading NBF files
"""

import struct
from pathlib import Path
from typing import Annotated, BinaryIO

import numpy as np


class PegasusNBFData:
    """Holds all the data loaded when loading a NBF file.

    It stores all the header data into private variables that are accessible via getters and stores the data arrays in a dictionary named `data` which is indexed via the variable field names in the NBF file.
    """

    def __init__(
        self,
        time: np.float64,
        num_meshblocks: int,
        list_of_variables: list[str],
        mesh_params: dict[str, np.float32 | int],
        meshblock_params: dict[str, int],
        *,
        big_endian: bool,
    ) -> None:
        """Initialize a PegasusNBFData class with the header data.

        Parameters
        ----------
        time : np.float64
            The simulation time in the file.
        big_endian : bool
            True if the data is big endian, False otherwise.
        num_meshblocks : int
            The number of mesh blocks.
        list_of_variables : list[str]
            The list of variables in the NBF files.
        mesh_params : dict[str, np.float32  |  int]
            The mesh parameters.
        meshblock_params : dict[str, int]
            The mesh block parameters.
        """
        # Header variables
        self.__time: np.float64 = time
        self.__big_endian: bool = big_endian
        self.__num_meshblocks: int = num_meshblocks
        self.__list_of_variables: list[str] = list_of_variables
        self.__mesh_params: dict[str, np.float32 | int] = mesh_params
        self.__meshblock_params: dict[str, int] = meshblock_params

        # The dictionary that actually stores the data
        self.data: Annotated[
            dict[str, np.typing.NDArray[np.float32]],
            "Contains the loaded data in a dictionary with keys matching the variable names in the HBF file.",
        ] = {}

        # Setup nbf_data.data member. Note that by the end of the reading these axis will be swapped to x1, x2, x3
        data_shape: tuple[int, int, int] = (
            int(self.mesh_params["nx3"]),
            int(self.mesh_params["nx2"]),
            int(self.mesh_params["nx1"]),
        )
        for key in self.list_of_variables:
            self.data[key] = np.empty(data_shape, dtype=np.float32)

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
        return len(self.__list_of_variables)

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
    time = np.float64(header_list[0].split()[-1])

    # Line 1: Endianness
    big_endian = bool(int(header_list[1].split()[-1]))

    # Line 2: The number of meshblocks
    num_meshblocks = int(header_list[2].split()[-1])

    # Line 3: The number of variables/fields stored in this file. Skipped since we
    # can get this with len(list_of_variables

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
        else:  # i.e. key[0] == "x":
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
        list_of_variables=list_of_variables,
        mesh_params=mesh_params,
        meshblock_params=meshblock_params,
    )


def _load_nbf_meshblock(
    nbf_file: BinaryIO,
    starting_offset: int,
    meshblock_header_size: int,
    nbf_data: PegasusNBFData,
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

    # Compute the indices to write to
    i_start = x1_block_coord * nbf_data.meshblock_params["nx1"]
    i_end = i_start + x1_block_size
    j_start = x2_block_coord * nbf_data.meshblock_params["nx2"]
    j_end = j_start + x2_block_size
    k_start = x3_block_coord * nbf_data.meshblock_params["nx3"]
    k_end = k_start + x3_block_size

    block_size = x1_block_size * x2_block_size * x3_block_size

    data = np.fromfile(
        nbf_file, dtype=np.float32, count=block_size * nbf_data.num_variables, offset=0
    )
    data = data.reshape(
        nbf_data.num_variables, x3_block_size, x2_block_size, x1_block_size
    )

    for nv in range(nbf_data.num_variables):
        field_key = nbf_data.list_of_variables[nv]

        nbf_data.data[field_key][k_start:k_end, j_start:j_end, i_start:i_end] = data[
            nv, :, :, :
        ]


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

        # Compute the required byte offsets and sizes needed to make each iteration independent

        # The size of the file header
        header_size = nbf_file.tell()
        # number of bytes per element
        element_width = 4
        # number of elements in the header in each meshblock
        meshblock_header_num_elements = 12
        # The size of the mesheblock header in bytes
        meshblock_header_size = element_width * meshblock_header_num_elements
        # The size of the entire meshblock in bytes
        meshblock_size = (
            meshblock_header_size
            + nbf_data.num_variables
            * element_width
            * (
                nbf_data.meshblock_params["nx1"]
                * nbf_data.meshblock_params["nx2"]
                * nbf_data.meshblock_params["nx3"]
            )
        )

        # loop over all meshblocks and read all variables
        for meshblock_id in range(nbf_data.num_meshblocks):
            _load_nbf_meshblock(
                nbf_file,
                meshblock_id * meshblock_size + header_size,
                meshblock_header_size,
                nbf_data,
            )

    # Swap axis so the data is formatted as (Nx1, Nx2, Nx3) and remove dimensions of length 1
    # Moving this into _load_nbf_meshblock causes a 30% slowdown
    for key in nbf_data.data:
        nbf_data.data[key] = np.swapaxes(nbf_data.data[key], 0, 2)
        nbf_data.data[key] = np.squeeze(nbf_data.data[key])

    return nbf_data
