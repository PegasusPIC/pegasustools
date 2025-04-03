"""Tests for the contents of loading_spectra.py."""

from pathlib import Path

import numpy as np

import pegasustools.loading_spectra as pt


def test__load_spectra() -> None:
    """Test pt._load_spectra."""
    # Setup paths
    file_path = Path("/Users/bc9754/Scratch/pegasus_test_files/slow.00088.spec")

    # Load fiducial data
    fiducial = pt.og_spectra_reader(file_path)

    # Load test data
    test = pt._load_spectra(file_path)

    np.testing.assert_array_max_ulp(fiducial, test, maxulp=0)

    print(fiducial.shape)
