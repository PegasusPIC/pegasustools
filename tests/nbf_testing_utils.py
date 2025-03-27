"""Utilities for testing portions of PegasusTools related to NBF files."""

import struct
from pathlib import Path

import numpy as np

import pegasustools as pt


def generate_random_nbf_file(
    path: Path, seed: int | None = None, dims: int = 3
) -> pt.PegasusNBFData:
    """Create a pt.PegasusNBFData object filled with random data and write it to a file. Only intended to help with testing.

    Parameters
    ----------
    path : Path
        The filepath to write the new .nbf file to
    seed : int | None, optional
        The seed to use for the PRNG, by default None which will use OS generated entropy
    dims : int, optional
        The number of dimensions of the data, by default 3

    Returns
    -------
    pt.PegasusNBFData
        The pt.PegasusNBFData object that was written to the file.
    """
    # Setup PRNG
    rng = np.random.default_rng(seed)

    # Determine the number of dimensions
    meshblock_params = {"nx1": 32, "nx2": 16, "nx3": 64}
    if dims < 3:  # noqa: PLR2004
        meshblock_params["nx3"] = 1
    if dims < 2:  # noqa: PLR2004
        meshblock_params["nx2"] = 1

    meshblock_per_side = 2
    size = meshblock_per_side * np.array(
        (meshblock_params["nx1"], meshblock_params["nx2"], meshblock_params["nx3"])
    )

    num_meshblocks = int(
        (size[0] / meshblock_params["nx1"])
        * (size[1] / meshblock_params["nx2"])
        * (size[2] / meshblock_params["nx3"])
    )

    # Create header data
    time = np.float64(rng.random(dtype=np.float64))
    list_of_variables = [
        "dens",
        "mom1",
        "mom2",
        "mom3",
        "Bcc1",
        "Bcc2",
        "Bcc3",
        "Ecc1",
        "Ecc2",
        "Ecc3",
    ]
    mesh_params: dict[str, np.float32 | int] = {
        "nx1": size[0],
        "x1min": np.float32(rng.random(dtype=np.float32)),
        "x1max": np.float32(rng.random(dtype=np.float32)),
        "nx2": size[1],
        "x2min": np.float32(rng.random(dtype=np.float32)),
        "x2max": np.float32(rng.random(dtype=np.float32)),
        "nx3": size[2],
        "x3min": np.float32(rng.random(dtype=np.float32)),
        "x3max": np.float32(rng.random(dtype=np.float32)),
    }

    nbf_data = pt.PegasusNBFData(
        time=time,
        big_endian=False,
        num_meshblocks=num_meshblocks,
        list_of_variables=list_of_variables,
        mesh_params=mesh_params,
        meshblock_params=meshblock_params,
    )

    # create arrays to write to .nbf file
    for key in list_of_variables:
        nbf_data.data[key] = rng.random(
            (int(mesh_params["nx1"]), int(mesh_params["nx2"]), int(mesh_params["nx3"])),
            dtype=np.float32,
        )

    create_nbf(path, nbf_data)

    return nbf_data


def create_nbf(filepath: Path, nbf_data: pt.PegasusNBFData) -> None:
    """Create an NBF file from a pt.PegasusNBFData object.

    This is intended solely as a tool to help with testing and, while I believe it is correct,
    it should not be used outside of testing PegasusTools.

    Parameters
    ----------
    filepath : Path
        The path to write the file to
    nbf_data : pt.PegasusNBFData
        The pt.PegasusNBFData object to write to the file
    """
    header = (
        f"Pegasus++ binary output at time = {nbf_data.time:.14e}\n"
        f"Big endian = {int(nbf_data.big_endian)}\n"
        f"Number of MeshBlocks = {nbf_data.num_meshblocks}\n"
        f"Number of variables = {len(nbf_data.list_of_variables)}\n"
        f"Variables:   {'   '.join(nbf_data.list_of_variables)}   \n"
        f"Mesh:   nx1={nbf_data.mesh_params['nx1']}   x1min={nbf_data.mesh_params['x1min']:.14e}   x1max={nbf_data.mesh_params['x1max']:.14e}\n"
        f"        nx2={nbf_data.mesh_params['nx2']}   x2min={nbf_data.mesh_params['x2min']:.14e}   x2max={nbf_data.mesh_params['x2max']:.14e}\n"
        f"        nx3={nbf_data.mesh_params['nx3']}   x3min={nbf_data.mesh_params['x3min']:.14e}   x3max={nbf_data.mesh_params['x3max']:.14e}\n"
        f"MeshBlock: nx1={nbf_data.meshblock_params['nx1']}   nx2={nbf_data.meshblock_params['nx2']}   nx3={nbf_data.meshblock_params['nx3']}\n"
    )

    with filepath.open(mode="wb") as nbf_file:
        # write the header
        nbf_file.write(header.encode("ascii"))

        # Loop through meshblocks and write them one at a time
        meshblock_i = int(
            nbf_data.mesh_params["nx1"] / nbf_data.meshblock_params["nx1"]
        )
        meshblock_j = int(
            nbf_data.mesh_params["nx2"] / nbf_data.meshblock_params["nx2"]
        )
        meshblock_k = int(
            nbf_data.mesh_params["nx3"] / nbf_data.meshblock_params["nx3"]
        )

        for i in range(meshblock_i):
            for j in range(meshblock_j):
                for k in range(meshblock_k):
                    # Write the header
                    meshblock_header = (
                        int(i),  # x1 coordinate of block
                        int(j),  # x2 coordinate of block
                        int(k),  # x3 coordinate of block
                        int(nbf_data.meshblock_params["nx1"]),  # x1 size of block
                        np.float32(0.0),  # min x1
                        np.float32(0.0),  # max x1
                        int(nbf_data.meshblock_params["nx2"]),  # x2 size of block
                        np.float32(0.0),  # min x2
                        np.float32(0.0),  # max x2
                        int(nbf_data.meshblock_params["nx3"]),  # x3 size of block
                        np.float32(0.0),  # min x3
                        np.float32(0.0),  # max x3
                    )
                    nbf_file.write(struct.pack("@4i2fi2fi2f", *meshblock_header))

                    # Write the data

                    # Compute the indices to write to
                    i_start = i * nbf_data.meshblock_params["nx1"]
                    i_end = i_start + nbf_data.meshblock_params["nx1"]
                    j_start = j * nbf_data.meshblock_params["nx2"]
                    j_end = j_start + nbf_data.meshblock_params["nx2"]
                    k_start = k * nbf_data.meshblock_params["nx3"]
                    k_end = k_start + nbf_data.meshblock_params["nx3"]

                    for key in nbf_data.list_of_variables:
                        subset = nbf_data.data[key][
                            i_start:i_end, j_start:j_end, k_start:k_end
                        ]
                        subset = np.swapaxes(subset, 0, 2)
                        subset.flatten().tofile(nbf_file)
