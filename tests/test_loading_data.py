"""Tests for the contents of loading_data.py."""

import re
from pathlib import Path

import nbf_testing_utils as pt_testing
import numpy as np
import pytest

import pegasustools as pt


@pytest.mark.parametrize("dims", [1, 2, 3])
def test_load_file_nbf(dims: int) -> None:
    """Test pt.load_file with 1D, 2D, & 3D nbf data."""
    # Setup paths
    file_path = Path(__file__).parent.resolve() / "data" / f"test_load_file_{dims}d.nbf"

    # Create test file & nbf_data
    fiducial_data = pt_testing.generate_random_nbf_file(file_path, seed=42, dims=dims)

    # # Load file my new function
    test_data = pt.load_file(file_path)

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


def test_load_file_file_does_not_exist() -> None:
    """Test for the exception that should appear if the file does not exist."""
    # Setup paths
    file_path = (
        Path(__file__).parent.resolve()
        / "data"
        / "test_load_file_file_does_not_exist.nbf"
    )

    err_msg = f"The file at {file_path} does not exist."
    with pytest.raises(FileNotFoundError, match=re.escape(err_msg)):
        pt.load_file(file_path)


def test_load_file_file_has_wrong_extension() -> None:
    """Test for the exception that should appear if the file does not have a Pegasus++ extension."""
    # Setup paths
    file_path = (
        Path(__file__).parent.resolve()
        / "data"
        / "test_load_file_file_has_wrong_extension.png"
    )

    file_path.open("wb").close()

    err_msg = f"The file {file_path} does not appear to be a Pegasus++ File."
    with pytest.raises(ValueError, match=re.escape(err_msg)):
        pt.load_file(file_path)
