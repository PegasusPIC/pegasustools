"""Tests for the contents of loading_spectra.py."""

import re
from pathlib import Path

import numpy as np
import pytest

import pegasustools as pt


def test_PegasusSpectralData_init() -> None:
    """Test pt.PegasusSpectralData constructor."""
    # Setup path
    file_path = (
        Path(__file__).parent.resolve() / "data" / "test_PegasusSpectralData.spec"
    )

    # Create the file
    time, fiducial_data = generate_random_spec_file(
        file_path, seed=42, num_meshblocks=7
    )

    # Load test data
    test = pt.PegasusSpectralData(file_path)

    # Verify the metadata
    assert time == test.time
    assert test.n_prp == 200
    assert test.n_prl == 400
    assert test.max_w_prp == 4.0
    assert test.max_w_prl == 4.0

    # Verify the spectra
    np.testing.assert_array_max_ulp(fiducial_data, test.data, maxulp=0)


def test_PegasusSpectralData_file_wrong_shape() -> None:
    """Test pt.PegasusSpectralData if the file is the wrong shape."""
    # Setup path
    file_path = (
        Path(__file__).parent.resolve()
        / "data"
        / "test_PegasusSpectralDat_wrong_shape.spec"
    )

    # Create the file
    time, fiducial_data = generate_random_spec_file(
        file_path, seed=42, num_meshblocks=7
    )

    n_prp = 17
    err_msg = (
        f"The file {file_path} does not have the right number of "
        "elements for the values of self.__n_prl = 400 and "
        f"self.__n_prp = {n_prp} provided."
    )
    with pytest.raises(ValueError, match=re.escape(err_msg)):
        _ = pt.PegasusSpectralData(file_path, n_prp=n_prp)


def test_PegasusSpectralData_average_spectra() -> None:
    """Test pt.PegasusSpectralData.average_spectra method."""
    # Setup path
    file_path = (
        Path(__file__).parent.resolve() / "data" / "test_PegasusSpectralData.spec"
    )

    # Create the file
    time, fiducial_data = generate_random_spec_file(
        file_path, seed=42, num_meshblocks=7
    )

    # Load test data
    test = pt.PegasusSpectralData(file_path)

    # Average the spectra
    test.average_spectra()

    # Compute the fiducial version
    summed_spectra = fiducial_data.sum(axis=0)
    norm = summed_spectra.sum()

    n_prp = 200
    max_w_prp = 4.0
    max_w_prl = 4.0

    spectra_prl = summed_spectra.sum(axis=0) / norm / (max_w_prl / n_prp)
    spectra_prp = summed_spectra.sum(axis=1) / norm / (max_w_prp / n_prp)

    # Verify the results
    assert test.spectra_prp.shape == (200,)
    assert test.spectra_prl.shape == (400,)
    np.testing.assert_array_max_ulp(spectra_prp, test.spectra_prp, maxulp=0)
    np.testing.assert_array_max_ulp(spectra_prl, test.spectra_prl, maxulp=0)


def generate_random_spec_file(
    file_path: Path,
    num_meshblocks: int,
    seed: int | None = None,
    num_parallel: int = 400,
    num_perpendicular: int = 200,
) -> tuple[float, np.typing.NDArray[np.float64]]:
    """Write a .spec file with random data for testing.

    Parameters
    ----------
    file_path : Path
        The path to the file to write.
    num_meshblocks : int
        The number of meshblocks
    seed : int | None, optional
        The seed for the PRNG, by default None which uses system entropy.
    num_parallel : int, optional
        n_prl from the peginput file, by default 400
    num_perpendicular : int, optional
        n_prp from the peginput file, by default 200

    Returns
    -------
    tuple[float, np.typing.NDArray[np.float64]]
        _description_
    """
    # Open file
    with file_path.open("wb") as spec_file:
        # Setup PRNG
        rng = np.random.default_rng(seed)

        # Write header
        time = rng.random()
        spec_file.write(
            (f"Particle distribution function at time = {time}\n").encode("ascii")
        )

        # Generate random data
        header_size = 6
        spec_data = rng.random(
            (num_meshblocks, header_size + num_perpendicular * num_parallel),
            dtype=np.float64,
        )

        # Save the data
        spec_data.flatten().tofile(spec_file)

        # trim off the header and reshape to the actual shape that the loader
        # will return
        spec_data = spec_data[:, header_size:]
        spec_data = spec_data.reshape((num_meshblocks, num_perpendicular, num_parallel))

    return time, spec_data
