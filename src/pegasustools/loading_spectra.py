"""Provides the utilities required to load output files from Pegasus++.

This module provides:
- PegasusSpectralData: A class for holding the data loaded from a spectra file
- _load_spectra: A function for loading spectra files
"""

import typing
from pathlib import Path

import numpy as np
import polars as pl


class PegasusSpectralData:
    """Holds all the data loaded when loading a spectra file.

    Stores the time data in a private variable accessible via a getter and stores the
    spectra data in a numpy array named `data`
    """

    def __init__(
        self,
        file_path: Path,
        n_prp: int = 200,
        n_prl: int = 400,
        max_w_prp: float = 4.0,
        max_w_prl: float = 4.0,
    ) -> None:
        """Initialize a PegasusSpectralData class with the header data.

        Parameters
        ----------
        file_path : Path
            The file path to the file to load
        n_prp : int, optional
            The value of n_prp used in the peginput file, by default 200. This argument
            is ignored if the spectra file is in the new format that contains this
            information in the header.
        n_prl : int, optional
            The value of n_prl used in the peginput file, by default 400. This argument
            is ignored if the spectra file is in the new format that contains this
            information in the header.
        max_w_prp : float, optional
            The value of max_w_prp used in the peginput file, by default 4.0. This
            argument is ignored if the spectra file is in the new format that contains
            this information in the header.
        max_w_prl : float, optional
            The value of max_w_prl used in the peginput file, by default 4.0. This
            argument is ignored if the spectra file is in the new format that contains
            this information in the header.

        Raises
        ------
        ValueError
            Raised if the file does not have the right number of elements for the
            provided n_prl and n_prp
        """
        # Define member variables
        self.__time: np.float64 = np.nan
        self.__num_ions: int = 1
        self.__n_prp: int | tuple[int, ...] = n_prp
        self.__n_prl: int | tuple[int, ...] = n_prl
        self.__max_w_prp: float | tuple[float, ...] = max_w_prp
        self.__max_w_prl: float | tuple[float, ...] = max_w_prl
        self.spectra_prp: np.typing.NDArray[np.float64]
        self.spectra_prl: np.typing.NDArray[np.float64]

        # Open the file
        with file_path.open(mode="rb") as spec_file:
            # Load the header
            self.__read_header(spec_file)

            # Load the entire remaining file
            self.data = np.fromfile(spec_file, dtype=np.float64)

        # Reshape the loaded data to extract the header and spectra in the correct shape
        if self.__num_ions == 1:
            self.__reshape_single_ion(file_path)
        else:
            self.__reshape_multiple_ion(file_path)

    def __read_header(self, spec_file: typing.BinaryIO) -> None:
        # Read in each line one by one until one of them isn't ASCII
        header = []
        while True:
            line_start = spec_file.tell()
            line = spec_file.readline()
            # Check if the line is ASCII or binary
            try:
                # Decode line to ascii and remove newline
                header.append(line.decode("ascii").rstrip())
            except UnicodeDecodeError:
                # Reset file to the beginning of this line
                spec_file.seek(line_start)
                break

        # Get time
        self.__time = float(header.pop(0).split()[-1])

        # Check for the old format
        if len(header) == 0:
            # This is the old header, it only contains the time
            return

        # Get the number of ion species if it's there
        if "Number of minor-ion species =" in header[0]:
            self.__num_ions = int(header.pop(0).split()[-1])

        # Select path based on the number of ions
        if self.__num_ions == 1:
            # This is a new header with a single ion
            self.__n_prl = int(header.pop(0).split()[-1])
            self.__n_prp = int(header.pop(0).split()[-1])
            self.__max_w_prl = float(header.pop(0).split()[-1])
            self.__max_w_prp = float(header.pop(0).split()[-1])
        else:
            # This is a new header with multiple ions
            # Loop through the header to read the data for each ion
            n_prl, n_prp, max_w_prl, max_w_prp = [], [], [], []
            for _ in range(self.__num_ions):
                n_prl.append(int(header.pop(0).split()[-1]))
                n_prp.append(int(header.pop(0).split()[-1]))
                max_w_prl.append(float(header.pop(0).split()[-1]))
                max_w_prp.append(float(header.pop(0).split()[-1]))

            # Copy the mutable lists to immutable tuples in member variables so they
            # can't be modified later
            self.__n_prl = tuple(n_prl)
            self.__n_prp = tuple(n_prp)
            self.__max_w_prl = tuple(max_w_prl)
            self.__max_w_prp = tuple(max_w_prp)

    def __reshape_single_ion(self, file_path: Path) -> None:
        assert isinstance(self.__n_prl, int)  # noqa: S101
        assert isinstance(self.__n_prp, int)  # noqa: S101

        # Get the info to reshape the array
        block_header_size = 6  # The header of each block is 6 elements
        num_row = self.__n_prl * self.__n_prp + block_header_size
        num_col = self.data.size // num_row

        # Check that the file is actually the right size for the number of elements
        # per spectra. Note that this check isn't perfect, it just verifies that the
        # file can be exactly divided by the number of elements provided.
        if self.data.size % num_row != 0:
            err_msg = (
                f"The file {file_path} does not have the right number of "
                f"elements for the values of {self.__n_prl = } and "
                f"{self.__n_prp = } provided."
            )
            raise ValueError(err_msg)

        # Rearrange the data into the correct shape including the header for each
        # meshblock
        self.data = self.data.reshape((num_col, num_row))

        # Slice off the header and main data
        headers = self.data[:, :block_header_size]
        self.data = self.data[:, block_header_size:]

        # Reshape data now that the headers have been removed
        self.data = self.data.reshape((num_col, self.__n_prp, self.__n_prl))

        # Organize the meshblock headers into a DataFrame
        self._meshblock_locations = pl.from_numpy(
            headers,
            schema=("x1min", "x1max", "x2min", "x2max", "x3min", "x3max"),
        )

    def __reshape_multiple_ion(self, file_path: Path) -> None:
        pass

    # Define getters for header variables
    @property
    def time(self) -> np.float64:
        """Get the simulation time of the spectra file.

        Returns
        -------
        np.float64
            The time in the spectra file
        """
        return self.__time

    @property
    def num_ions(self) -> int:
        """Get the number of ions in this file.

        Returns
        -------
        int
            The number of ions in the spectra file
        """
        return self.__num_ions

    @property
    def n_prp(self) -> int | tuple[int, ...]:
        """Get n_prp.

        Returns
        -------
        int | tuple[int, ...]
            The value(s) of n_prp
        """
        return self.__n_prp

    @property
    def n_prl(self) -> int | tuple[int, ...]:
        """Get n_prl.

        Returns
        -------
        int | tuple[int, ...]
            The value(s) of n_prl
        """
        return self.__n_prl

    @property
    def max_w_prp(self) -> float | tuple[float, ...]:
        """Get max_w_prp.

        Returns
        -------
        float | tuple[float, ...]
            The value(s) of max_w_prp
        """
        return self.__max_w_prp

    @property
    def max_w_prl(self) -> float | tuple[float, ...]:
        """Get max_w_prl.

        Returns
        -------
        float | tuple[float, ...]
            The value(s) of max_w_prl
        """
        return self.__max_w_prl

    @property
    def meshblock_locations(self) -> pl.DataFrame:
        """Get meshblock locations DataFrame.

        Returns
        -------
        pl.DataFrame
            The location data for each meshblock. Keys are:
            - x1min
            - x1max
            - x2min
            - x2max
            - x3min
            - x3max
        """
        return self._meshblock_locations

    def reduce_spectra(self) -> None:
        """Reduce the spectra.

        Creates two new member variables, spectra_prl and spectra_prp, with
        the parallel and perpendicular averaged spectrum. Depends on `max_w_prp`,
        `max_w_prl`, `n_prp`, and `n_prl` being set correctly.
        """
        summed_spectra = self.data.sum(axis=0)

        # v_prl array goes from [-vprlmax to vprlmax]
        dv_prl = 2.0 * self.__max_w_prl / self.__n_prl
        # w_prp array goes from [0 to vprpmax]
        dw_prp = self.__max_w_prp / self.__n_prp
        norm = summed_spectra.sum() * dv_prl * dw_prp

        # normalized, averaged f(wprl,wprp) such that int(f(wprl,wprp) dwprl dwprp) = 1
        # Note: this is not the correct normalization for edotv outputs (edotv should be
        # normalized relative to f, not itself)
        data_avg = summed_spectra / norm
        half_bin = (self.__max_w_prp / self.__n_prp) / 2
        w_prp = np.linspace(0 + half_bin, self.__max_w_prp + half_bin, self.__n_prp)

        self.spectra_prl = data_avg.sum(axis=0) * dw_prp
        self.spectra_prp = 0.5 * (data_avg.sum(axis=1) / w_prp) * dv_prl
