"""Tests for the contents of loading_data.py."""

import pathlib

import numpy as np

import pegasustools as pt


def test__load_nbf() -> None:
    """Preliminary test for pt._load_nbf."""
    # Setup paths
    slow2_file_path = pathlib.Path(
        "/Users/bc9754/Scratch/pegasus_test_files/slow.out2.00883.nbf"
    )

    # Load file with Hima's script
    fid_data = pt.hima_nbf(slow2_file_path)

    # Load file my new function
    test_data = pt._load_nbf(slow2_file_path)  # noqa: SLF001

    # Compare
    for key in test_data.data:
        fid_field = fid_data[key]
        test_field = test_data.data[key]

        # check the sizes are the same
        assert fid_field.shape == test_field.shape

        # check that all elements are correct
        np.testing.assert_array_max_ulp(fid_field, test_field, maxulp=0)
