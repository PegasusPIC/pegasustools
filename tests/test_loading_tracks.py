"""Tests for the contents of loading_tracks.py."""

import re
from pathlib import Path

import numpy as np
import polars as pl
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

    err_msg = (
        f"The file at {file_path} with extension ['.txt'] is not a "
        "Pegasus++ tracked particle file."
    )
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


def test_collate_tracks_from_ascii() -> None:
    """Test the collate_tracks_from_ascii function."""
    # Setup paths
    source_directory = (
        Path(__file__).parent.resolve() / "data" / "collate_tracks_from_ascii"
    )
    source_directory.mkdir(exist_ok=True)
    test_path_default = source_directory / "problem_collated_tracks.hdf5"
    test_path_custom = source_directory / "custom_name.hdf5"

    # Delete the HDF5 files if they exist
    if test_path_default.exists():
        test_path_default.unlink()
    if test_path_custom.exists():
        test_path_custom.unlink()

    # Generate the data
    fid_data = {}
    for block_id in range(2):
        for particle_id in range(3):
            key = f"{block_id}-{particle_id}"
            fid_data[key] = generate_random_track_ascii(
                source_directory / f"problem.0{particle_id}.0000{block_id}.track.dat",
                generate_mu=True,
            )

    # Collate the test data
    # Using default destination path
    pt.collate_tracks_from_ascii(source_directory)
    # Using custom destination path
    pt.collate_tracks_from_ascii(source_directory, test_path_custom)

    # Check correctness
    for key in fid_data:
        for test_path in [test_path_custom, test_path_default]:
            block_id = fid_data[key][0]
            particle_id = fid_data[key][1]
            test = pt.PegasusTrack(test_path, block_id, particle_id)

            assert test.block_id == block_id
            assert test.particle_id == particle_id

            for i, field in enumerate(test.data.dtype.names):
                if field == "mu":
                    np.testing.assert_allclose(
                        fid_data[key][2][:, i].astype(np.float32),
                        test.data[field].astype(np.float32),
                        rtol=0.03,
                    )
                else:
                    np.testing.assert_array_max_ulp(
                        fid_data[key][2][:, i].astype(np.float32),
                        test.data[field].astype(np.float32),
                        maxulp=10,
                    )


def test_collate_tracks_from_ascii_no_directory() -> None:
    """Test the collate_tracks_from_ascii function."""
    # Setup path
    source_directory = Path("/fake/path/here")

    err_msg = f"{source_directory} is not a directory or does not exist."
    with pytest.raises(ValueError, match=re.escape(err_msg)):
        pt.collate_tracks_from_ascii(source_directory)


def generate_random_track_ascii(
    file_path: Path, seed: int | None = None, *, generate_mu: bool = False
) -> tuple[int, int, np.typing.NDArray[np.float32]]:
    """Generate a .track.dat ASCII file.

    Parameters
    ----------
    file_path : Path
        The path to write the file to
    seed : int | None, optional
        The seed for the PRNG, by default None
    generate_mu: bool, optional
        Compute the magnetic moment as well

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

    if generate_mu:
        # Add the mu data

        # specific velocities
        specific_velocities = track_data[:, 3:6] - track_data[:, 12:15]

        # Magnetic fields
        magnetic_fields = track_data[:, 6:9]

        velocities_sqr = (specific_velocities**2).sum(axis=1)
        magnetic_magnitude = np.sqrt((magnetic_fields**2).sum(axis=1))

        # specific field-parallel velocity
        velocity_prl = (specific_velocities * magnetic_fields).sum(
            axis=1
        ) / magnetic_magnitude

        # mu invariant
        mu = 0.5 * (velocities_sqr - velocity_prl**2) / magnetic_magnitude

        track_data = np.hstack((track_data, mu.reshape(len(mu), 1)))

    return (
        int(block_id),
        int(particle_id),
        track_data,
    )


def generate_random_track_binary(  # noqa: PLR0915
    file_path: Path,
    num_columns: int,
    seed: int | None = None,
) -> pl.DataFrame:
    """Generate a .track.dat ASCII file.

    Parameters
    ----------
    file_path : Path
        The path to write the file to
    num_columns : int
        The number of columns to write
    seed : int | None, optional
        The seed for the PRNG, by default None

    Returns
    -------
    tuple[int, int, np.typing.NDArray[np.float32]]
        The data written to the binary file.
    """
    # Setup PRNG
    rng = np.random.default_rng(seed)

    # Open file
    with file_path.open("wb") as track_file:
        # Write header
        time = rng.uniform(0, 1000, 1)[0]
        header = f"Particle track output function at time = {time}\n"
        track_file.write(header.encode("ascii"))

        # Generate random data
        length = 1000
        track_data = rng.uniform(-1, 10, num_columns * length)
        track_data = track_data.reshape((length, num_columns))

        # Modify the three id columns
        track_data[:, 0] = np.floor(track_data[:, 0]) + 0.001
        track_data[:, 1] = np.floor(track_data[:, 1]) + 0.001
        track_data[:, 2] = np.floor(track_data[:, 2]) + 0.001

        # Save the data
        track_data.tofile(track_file)

    # ===== Add the mu data =====

    # Compute v, B, and U indices.
    v_start = 7
    b_start = 10
    u_start = 16
    match num_columns:
        case 18 | 21:  # 1D
            v_start = v_start - 2
            b_start = b_start - 2
            u_start = u_start - 2
        case 19 | 22:  # 2D
            v_start = v_start - 1
            b_start = b_start - 1
            u_start = u_start - 1
        case 20 | 23:  # 3D
            pass

    # specific velocities
    specific_velocities = (
        track_data[:, v_start : v_start + 3] - track_data[:, u_start : u_start + 3]
    )

    # Magnetic fields
    magnetic_fields = track_data[:, b_start : b_start + 3]

    velocities_sqr = (specific_velocities**2).sum(axis=1)
    magnetic_magnitude = np.sqrt((magnetic_fields**2).sum(axis=1))

    # specific field-parallel velocity
    velocity_prl = (specific_velocities * magnetic_fields).sum(
        axis=1
    ) / magnetic_magnitude

    # mu invariant
    mu = 0.5 * (velocities_sqr - velocity_prl**2) / magnetic_magnitude

    track_data = np.hstack((track_data, mu.reshape(len(mu), 1)))

    # ===== Convert to dataframe =====
    int_t = pl.datatypes.Int64
    float_t = pl.datatypes.Float64
    column_schema = [
        ("particle_id", int_t),
        ("block_id", int_t),
        ("species", int_t),
        ("time", float_t),
        ("x1", float_t),
        ("x2", float_t),
        ("x3", float_t),
        ("v1", float_t),
        ("v2", float_t),
        ("v3", float_t),
        ("B1", float_t),
        ("B2", float_t),
        ("B3", float_t),
        ("E1", float_t),
        ("E2", float_t),
        ("E3", float_t),
        ("U1", float_t),
        ("U2", float_t),
        ("U3", float_t),
        ("dens", float_t),
        ("forcing1", float_t),
        ("forcing2", float_t),
        ("forcing3", float_t),
        ("mu", float_t),
    ]

    match num_columns:
        case 18:  # 1D no forcing
            column_schema.remove(("x2", float_t))
            column_schema.remove(("x3", float_t))
            column_schema.remove(("forcing1", float_t))
            column_schema.remove(("forcing2", float_t))
            column_schema.remove(("forcing3", float_t))
        case 19:  # 2D no forcing
            column_schema.remove(("x3", float_t))
            column_schema.remove(("forcing1", float_t))
            column_schema.remove(("forcing2", float_t))
            column_schema.remove(("forcing3", float_t))
        case 20:  # 3D no forcing
            column_schema.remove(("forcing1", float_t))
            column_schema.remove(("forcing2", float_t))
            column_schema.remove(("forcing3", float_t))
        case 21:  # 1D with forcing
            column_schema.remove(("x2", float_t))
            column_schema.remove(("x3", float_t))
        case 22:  # 2D with forcing
            column_schema.remove(("x3", float_t))
        case 23:  # 3D with forcing
            pass

    return pl.from_numpy(track_data, schema=column_schema)
