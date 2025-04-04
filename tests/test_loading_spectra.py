"""Tests for the contents of loading_spectra.py."""

from pathlib import Path

import numpy as np

import pegasustools as pt


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

    return time, spec_data[:, 6:]


def test__load_spectra() -> None:
    """Test pt._load_spectra."""
    # Setup path
    file_path = Path(__file__).parent.resolve() / "data" / "test__load_spectra.spec"

    # Create the file
    time, fiducial_data = generate_random_spec_file(
        file_path, seed=42, num_meshblocks=7
    )

    # Load test data
    test = pt.PegasusSpectralData(file_path)

    np.testing.assert_array_max_ulp(fiducial_data, test.data, maxulp=0)
