"""Tests for the contents of loading_spectra.py."""

from pathlib import Path

import numpy as np

import pegasustools as pt


def test__load_spectra() -> None:
    """Test pt._load_spectra."""
    # Setup paths
    file_path = Path("/Users/bc9754/Scratch/pegasus_test_files/slow.00088.spec")

    # Load test data
    test = pt.PegasusSpectralData(file_path)

    # Load fiducial data
    fiducial = pt.og_spectra_reader(file_path)

    np.testing.assert_array_max_ulp(fiducial, test.data, maxulp=0)


def test__load_spectra_and_sum() -> None:
    """Test pt._load_spectra."""
    # Setup paths
    file_path = Path("/Users/bc9754/Scratch/pegasus_test_files/slow.00088.spec")

    # Load test data
    test = pt.PegasusSpectralData(file_path)
    summed_spectra = test.sum_over_meshblocks()

    # Load fiducial data
    fiducial = pt.og_spectra_reader_with_sum(file_path)

    np.testing.assert_array_max_ulp(fiducial, summed_spectra, maxulp=0)
