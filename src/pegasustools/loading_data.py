"""Provides the utilities required to load output files from Pegasus++.

This module provides:
- FUNCTION/CLASS NAME: DESCRIPTION
"""

import struct
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
        # Header variables
        self.__time: np.float32 = time
        self.__big_endian: bool = big_endian
        self.__num_meshblocks: int = num_meshblocks
        self.__num_variables: int = num_variables
        self.__list_of_variables: list[str] = list_of_variables
        self.__mesh_params: dict[str, np.float32 | int] = mesh_params
        self.__meshblock_params: dict[str, int] = meshblock_params

        # The dictionary that actually stores the data
        self.data: dict[str, np.typing.NDArray[np.float32]] = {}

        # Setup nbf_data.data member
        data_shape: tuple[int, int, int] = (
            int(self.mesh_params["nx3"]),
            int(self.mesh_params["nx2"]),
            int(self.mesh_params["nx1"]),
        )
        for key in self.list_of_variables:
            self.data[key] = np.empty(data_shape, dtype=np.float32)

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

        # starting indices for each logical location
        islist = np.arange(
            0, nbf_data.mesh_params["nx1"], nbf_data.meshblock_params["nx1"]
        )
        jslist = np.arange(
            0, nbf_data.mesh_params["nx2"], nbf_data.meshblock_params["nx2"]
        )
        kslist = np.arange(
            0, nbf_data.mesh_params["nx3"], nbf_data.meshblock_params["nx3"]
        )

        # loop over all meshblocks and read all variables
        for nb in range(nbf_data.num_meshblocks):
            il1 = struct.unpack("@i", nbf_file.read(4))[0]
            il2 = struct.unpack("@i", nbf_file.read(4))[0]
            il3 = struct.unpack("@i", nbf_file.read(4))[0]
            mx1 = struct.unpack("@i", nbf_file.read(4))[0]
            minx1 = struct.unpack("@f", nbf_file.read(4))[0]
            maxx1 = struct.unpack("@f", nbf_file.read(4))[0]
            mx2 = struct.unpack("@i", nbf_file.read(4))[0]
            minx2 = struct.unpack("@f", nbf_file.read(4))[0]
            maxx2 = struct.unpack("@f", nbf_file.read(4))[0]
            mx3 = struct.unpack("@i", nbf_file.read(4))[0]
            minx3 = struct.unpack("@f", nbf_file.read(4))[0]
            maxx3 = struct.unpack("@f", nbf_file.read(4))[0]
            iis = islist[il1]
            iie = iis + mx1
            ijs = jslist[il2]
            ije = ijs + mx2
            iks = kslist[il3]
            ike = iks + mx3
            fmt = "@%df" % (mx1 * mx2 * mx3)
            for nv in range(nbf_data.num_variables):
                tmp = nbf_data.data[nbf_data.list_of_variables[nv]]
                data = struct.unpack(fmt, nbf_file.read(4 * mx1 * mx2 * mx3))
                data = np.array(data)
                data = data.reshape(mx3, mx2, mx1)
                tmp[iks:ike, ijs:ije, iis:iie] = data

    # Swap axis so the data is formatted as (Nx1, Nx2, Nx3)
    for key in nbf_data.data:
        nbf_data.data[key] = np.swapaxes(nbf_data.data[key], 0, 2)

    return nbf_data
