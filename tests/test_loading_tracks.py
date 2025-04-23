"""Tests for the contents of loading_tracks.py."""

import re
from pathlib import Path

import numpy as np
import pytest

import pegasustools as pt


def test_PegasusTrack_ASCII() -> None:
    """Test the PegasusTrack constructor with an ASCII file."""
    # Setup path
    file_path = (
        Path(__file__).parent.resolve() / "data" / "test_PegasusTrack_ASCII.track.dat"
    )

    # Generate the data
    fid_block_id, fid_particle_id, fid_data = generate_random_track_ascii(file_path)

    # Load test data
    test = pt.PegasusTrack(file_path)

    print(test.data.shape)
    print(test.data[0])

    # Check correctness
    assert test.block_id == fid_block_id
    assert test.particle_id == fid_particle_id

    for i, field in enumerate(test.data.dtype.names):
        np.testing.assert_array_max_ulp(
            fid_data[:, i].astype(np.float32),
            test.data[field].astype(np.float32),
            maxulp=10,
        )


def test_PegasusTrack_ASCII_not_pegasus_file() -> None:
    """Test for the exception that should appear if the file has the wrong header."""
    # Setup paths
    file_path = Path(__file__).parent.resolve() / "data" / "wrong_header.track.dat"
    with file_path.open("w") as file:
        file.write("this is not the correct header\n")

    err_msg = f"The file at {file_path} is not a Pegasus++ .track.dat file."
    with pytest.raises(RuntimeError, match=re.escape(err_msg)):
        pt.PegasusTrack(file_path)


def test_PegasusTrack_wrong_extension() -> None:
    """Test for the exception that should appear if the file has the wrong extension."""
    # Setup paths
    file_path = Path(__file__).parent.resolve() / "data" / "wrong_extension.txt"
    with file_path.open("w") as file:
        file.write("this is placeholder text\n")

    err_msg = f"The file at {file_path} is not a Pegasus++ tracked particle file."
    with pytest.raises(RuntimeError, match=re.escape(err_msg)):
        pt.PegasusTrack(file_path)


def test_PegasusTrack_bad_ids() -> None:
    """Test for exception when missing or bad arguments.

    Test for the exception that should appear when trying to load the collated HDF5 file
    without block or particle IDs or if those IDs are negative
    """
    # Setup paths
    file_path = Path(__file__).parent.resolve() / "data" / "wrong_ids.hdf5"
    with file_path.open("w") as file:
        file.write("this is placeholder text\n")

    err_msg = (
        "block_id and particle_id are required when loading a dataset from "
        "a collated HDF5 file and they both must be positive ints."
    )

    # ===== Tests for missing args =====

    # Missing both
    with pytest.raises(ValueError, match=re.escape(err_msg)):
        pt.PegasusTrack(file_path)

    # Missing block_id
    with pytest.raises(ValueError, match=re.escape(err_msg)):
        pt.PegasusTrack(file_path, block_id=10)

    # Missing particle_id
    with pytest.raises(ValueError, match=re.escape(err_msg)):
        pt.PegasusTrack(file_path, particle_id=10)

    # ===== Tests for negative args =====

    # Both negative
    with pytest.raises(ValueError, match=re.escape(err_msg)):
        pt.PegasusTrack(file_path, block_id=-10, particle_id=-10)

    # block_id negative
    with pytest.raises(ValueError, match=re.escape(err_msg)):
        pt.PegasusTrack(file_path, block_id=-10)

    # particle_id negative
    with pytest.raises(ValueError, match=re.escape(err_msg)):
        pt.PegasusTrack(file_path, particle_id=-10)


def generate_random_track_ascii(
    file_path: Path, seed: int | None = None
) -> tuple[int, int, np.typing.NDArray[np.float32]]:
    """Generate a .track.dat ASCII file.

    Parameters
    ----------
    file_path : Path
        The path to write the file to
    seed : int | None, optional
        The seed for the PRNG, by default None

    Returns
    -------
    tuple[int, int, np.typing.NDArray[np.float32]]
        The data written to the ASCII file. Note that errors up to 7 ULP have been
        observed in the write/read process.
    """
    # Setup PRNG
    rng = np.random.default_rng(seed)

    particle_id = rng.integers(1000)
    block_id = rng.integers(100)

    header = (
        f"# Pegasus++ track data for particle with id={particle_id} and mid={block_id}\n"  # noqa: E501
        "# [1]=time     [2]=x1       [3]=x2       [4]=v1       [5]=v2       [6]=v3       [7]=B1       [8]=B2       [9]=B3       [10]=E1       [11]=E2       [12]=E3       [13]=U1       [14]=U2       [15]=U3       [16]=dens\n"  # noqa: E501
    )

    # Open file
    with file_path.open("w") as track_file:
        # Write header
        track_file.write(header)

        # Generate random data
        width = 16
        length = 1000
        track_data = rng.uniform(-1, 1, (width - 1) * length).astype(np.float32)
        track_data = track_data.reshape((length, (width - 1)))

        # Add on the time
        times = np.linspace(0, 10000, num=length).reshape(length, 1)
        track_data = np.append(times, track_data, axis=1)

        # Simulate a restart
        restart_section = track_data[-100:, :]
        track_data_restarted = np.concatenate((track_data, restart_section), axis=0)

        # Save the data
        np.savetxt(track_file, track_data_restarted, delimiter=" ", fmt="%-8.6e")

    return (
        int(block_id),
        int(particle_id),
        track_data,
    )
