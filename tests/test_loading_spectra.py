"""Tests for the contents of loading_spectra.py."""

from pathlib import Path

import numpy as np

import pegasustools as pt


def test__load_spectra() -> None:
    """Test pt._load_spectra."""
    # Setup paths
    file_path = Path("/Users/bc9754/Scratch/pegasus_test_files/slow.00088.spec")

    # Load fiducial data
    fiducial = pt.og_spectra_reader(file_path)

    # Load test data
    test = pt.PegasusSpectralData(file_path)

    np.testing.assert_array_max_ulp(fiducial, test.data, maxulp=0)
