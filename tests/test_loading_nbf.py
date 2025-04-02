"""Tests for the contents of loading_nbf.py."""

import re
from pathlib import Path

import nbf_testing_utils as pt_testing
import numpy as np
import pytest

import pegasustools.loading_nbf as pt


@pytest.mark.parametrize("dims", [1, 2, 3])
def test__load_nbf(dims: int) -> None:
    """Test pt._load_nbf with 1D, 2D, & 3D data."""
    # Setup paths
    file_path = Path(__file__).parent.resolve() / "data" / f"test__load_nbf_{dims}d.nbf"

    # Create test file & nbf_data
    fiducial_data = pt_testing.generate_random_nbf_file(file_path, seed=42, dims=dims)

    # # Load file my new function
    test_data = pt._load_nbf(file_path)

    # Compare header data
    np.testing.assert_array_max_ulp(fiducial_data.time, test_data.time, maxulp=3)
    assert fiducial_data.big_endian == test_data.big_endian
    assert fiducial_data.num_meshblocks == test_data.num_meshblocks
    assert fiducial_data.list_of_variables == test_data.list_of_variables
    assert fiducial_data.mesh_params == test_data.mesh_params
    assert fiducial_data.meshblock_params == test_data.meshblock_params

    # Compare field data
    for key in test_data.data:
        fid_field = fiducial_data.data[key]
        test_field = test_data.data[key]

        # check the sizes are the same
        assert fid_field.shape == test_field.shape

        # check that all elements are correct
        np.testing.assert_array_max_ulp(np.squeeze(fid_field), test_field, maxulp=0)


def test__load_nbf_file_too_small() -> None:
    """Test for the exception that should appear if the file is too small."""
    # Setup paths
    file_path = Path(__file__).parent.resolve() / "data" / "too_short.nbf"
    with file_path.open("wb") as file:
        file.write(b"not\nenough\nlines")

    err_msg = f"{file_path} is not a Pegasus++ NBF file."
    with pytest.raises(OSError, match=re.escape(err_msg)):
        pt._load_nbf(file_path)


def test__load_nbf_file_wrong_first_line() -> None:
    """Test for the exception that should appear if the file doesn't start with the correct line."""
    # Setup paths
    file_path = Path(__file__).parent.resolve() / "data" / "too_short.nbf"
    with file_path.open("wb") as file:
        file.write(
            b"line 1\nline 2\nline 3\nline 4\nline 5\nline 6\nline 7\nline 8\nline 9\n"
        )

    err_msg = f"{file_path} is not a Pegasus++ NBF file."
    with pytest.raises(OSError, match=re.escape(err_msg)):
        pt._load_nbf(file_path)
