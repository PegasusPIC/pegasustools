"""Provides the utilities required to load output files from Pegasus++.

This module provides:
- FUNCTION/CLASS NAME: DESCRIPTION
"""

from pathlib import Path
from typing import BinaryIO

import numpy as np


def _load_nbf_header(
    nbf_file: BinaryIO,
) -> dict[
    str,
    np.float64 | bool | int | list[str] | dict[str, np.float64 | int] | dict[str, int],
]:
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
    header_dict: dict[
        str,
        np.float64
        | bool
        | int
        | list[str]
        | dict[str, np.float64 | int]
        | dict[str, int],
    ] = {}

    # Line 0: The time of the output
    header_dict["time"] = np.float64(header_list[0].split()[-1])

    # Line 1: Endianness
    header_dict["big_endian"] = bool(int(header_list[1].split()[-1]))

    # Line 2: The number of meshblocks
    header_dict["num_meshblocks"] = int(header_list[2].split()[-1])

    # Line 3: The number of variables/fields stored in this file
    header_dict["num_variables"] = int(header_list[3].split()[-1])

    # Line 4: The list of variables
    header_dict["list_of_variables"] = list(header_list[4].split()[1:])

    # Line 5-7: The mesh variables
    # Combine all three lines, split at whitespace, and discard the "Mesh:" part of the line
    combined_lines = (header_list[5] + header_list[6] + header_list[7]).split()[1:]
    # Loop through elements to build a dictionary with values and keys
    mesh_dict: dict[str, np.float64 | int] = {}
    for element in combined_lines:
        key, value = element.split("=")
        if key[:2] == "nx":
            mesh_dict[key] = int(value)
        elif key[0] == "x":
            mesh_dict[key] = np.float64(value)
    header_dict["mesh"] = mesh_dict

    # Line 8: Get the meshblock variables
    meshblock_dict: dict[str, int] = {}
    for element in header_list[8].split()[1:]:
        key, value = element.split("=")
        meshblock_dict[key] = int(value)
    header_dict["meshblock"] = meshblock_dict

    return header_dict


def _load_nbf(filepath: Path) -> str:
    # Open the file
    with filepath.open(mode="rb") as nbf_file:
        # Read the header
        header = _load_nbf_header(nbf_file)

        # META: Read the binary part of the file
        return header
