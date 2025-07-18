"""Provides the utilities required to load .hst files from Pegasus++."""

from pathlib import Path

import numpy as np
import polars as pl


def load_hst_file(hst_path: Path) -> pl.DataFrame:
    r"""Load the contents of a .hst files as a Polars dataframe.

    Parameters
    ----------
    hst_path : Path
        The path to the .hst file

    Returns
    -------
    pl.DataFrame
        The Polars dataframe that contains the data from the .hst file. Note that the
        contents are all in FP32 since the .hst files don't contain enough precision for
        FP64.

    Raises
    ------
    RuntimeError
        Raised if the .hst files doesn't have the proper header. Namely it checks that
        the first line is '# Athena++ history data\n' as a quick indicator if this is
        the proper file type.
    """
    # ===== Get the column names =====
    # load the header lines
    with hst_path.open("r") as hst_file:
        title = next(hst_file)
        header = next(hst_file)

    # Verify title
    if title != "# Athena++ history data\n":
        msg = (
            f"The file at {hst_path} does not have the correct header to be a hst file."
        )
        raise RuntimeError(msg)

    # Extract column names from the header
    column_names = [col_name.split("=")[1] for col_name in header.split()[1:]]

    # ===== Load data =====
    hst_arr = np.loadtxt(hst_path, dtype=np.float32)

    # ===== Convert to Polars dataframe =====
    return pl.from_numpy(hst_arr, column_names)
