"""Provides the utilities required to load output files from Pegasus++.

This module provides:
- PegasusSpectralData: A class for holding the data loaded from a spectra file
- _load_spectra: A function for loading spectra files
"""

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
        self.__n_prp: int | list[int] = n_prp
        self.__n_prl: int | list[int] = n_prl
        self.__max_w_prp: float | list[float] = max_w_prp
        self.__max_w_prl: float | list[float] = max_w_prl
        self.spectra_prp: np.typing.NDArray[np.float64]
        self.spectra_prl: np.typing.NDArray[np.float64]

        # Open the file
        with file_path.open(mode="rb") as spec_file:
            # Load the header
            ascii_header: list[str] = []
            while True:
                reset_location = spec_file.tell()
                try:
                    ascii_header.append(spec_file.readline().decode("ascii").rstrip())
                except UnicodeDecodeError:
                    spec_file.seek(reset_location)
                    break

            # Load the entire remaining file
            self.data = np.fromfile(spec_file, dtype=np.float64)

        # Now that we have the data and the header we'll pass it off to routines for
        # spec files and for specav style files
        if file_path.suffix == ".spec":
            self.__file_type = "spec"
            self.__num_ions = 1
            self.__process_spec_files(file_path, ascii_header)
        elif file_path.suffix in [
            ".specav",
            ".edotv_prl_av",
            ".edotv_prp_av",
            ".spec_fpc",
            ".edotv_prl_fpc",
            ".edotv_prp_fpc",
        ]:
            self.__file_type = "specav"
            self.__process_specav_files(file_path, ascii_header)
        else:
            msg = f"Error: {file_path} is not a spectra file."
            raise RuntimeError(msg)

    def __process_spec_files(self, file_path: Path, ascii_header: list[str]) -> None:
        """Process .spec files.

        Parameters
        ----------
        file_path : Path
            The path to the spec file
        ascii_header : list[str]
            The ascii header to the file.

        Raises
        ------
        ValueError
            Thrown if the dataset is not the right size for the provided n_prp and n_prl
        """
        self.__time = np.float32(ascii_header[0].split()[-1])

        # Check if this is the new spectra format with the complete header
        if len(ascii_header) > 1:
            # This is the new header type
            self.__n_prl = int(ascii_header[1].split(" ")[-1])
            self.__n_prp = int(ascii_header[2].split(" ")[-1])
            self.__max_w_prl = float(ascii_header[3].split(" ")[-1])
            self.__max_w_prp = float(ascii_header[4].split(" ")[-1])

        # Type narrowing
        assert isinstance(self.__n_prl, int)  # noqa: S101
        assert isinstance(self.__n_prp, int)  # noqa: S101
        assert isinstance(self.__max_w_prl, float)  # noqa: S101
        assert isinstance(self.__max_w_prp, float)  # noqa: S101

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

    def __process_specav_files(self, file_path: Path, ascii_header: list[str]) -> None:
        """Process .specav files.

        Parameters
        ----------
        file_path : Path
            The path to the file
        ascii_header : list[str]
            The ascii header to the file.

        Raises
        ------
        ValueError
            Thrown if the dataset is not the right size for the provided n_prp and n_prl
        """
        self.__time = np.float32(ascii_header[0].split()[-1])

        # Check if this file has more than one ion species
        if len(ascii_header) == 1:
            # The file contains a single ion species
            self.__num_ions = 1
        else:
            # The file contains more than one ion species

            # Get the number of minor ions and add 1 to get the total number of ion
            # species
            self.__num_ions = int(ascii_header[1].split()[-1]) + 1

            self.__n_prp = []
            self.__n_prl = []
            self.__max_w_prp = []
            self.__max_w_prl = []
            for i in range(self.__num_ions):
                start_idx = i * 4 + 2
                self.__n_prl.append(int(ascii_header[start_idx].split()[-1]))
                self.__n_prp.append(int(ascii_header[start_idx + 1].split()[-1]))
                self.__max_w_prp.append(float(ascii_header[start_idx + 2].split()[-1]))
                self.__max_w_prl.append(float(ascii_header[start_idx + 3].split()[-1]))

        # Type narrowing
        assert isinstance(self.__n_prl, list)  # noqa: S101
        assert isinstance(self.__n_prp, list)  # noqa: S101
        assert isinstance(self.__max_w_prl, list)  # noqa: S101
        assert isinstance(self.__max_w_prp, list)  # noqa: S101

        # Check that the file is actually the right size for the number of elements
        # per spectra. Note that this check isn't perfect, it just verifies that the
        # file can be exactly divided by the number of elements provided.
        data_size = 0
        for i in range(self.__num_ions):
            data_size += self.__n_prl[i] * self.__n_prp[i]

        if self.data.size != data_size:
            err_msg = (
                f"The file {file_path} does not have the right number of "
                f"elements for the values of {self.__n_prl = } and "
                f"{self.__n_prp = } provided."
            )
            raise ValueError(err_msg)

        # Now that we've got the header data sorted out it's time to deal with the
        # spectral data. We'll slice off each spectra, reshape it, then copy collect it
        # with the other chunks in self.data
        current_start = 0
        new_data = []
        for i in range(self.__num_ions):
            chunk_size = self.__n_prl[i] * self.__n_prp[i]
            data_chunk = self.data[current_start : current_start + chunk_size]
            data_chunk = data_chunk.reshape((self.__n_prp[i], self.__n_prl[i]))
            new_data.append(data_chunk)
            current_start += chunk_size

        # Assign to self.data
        self.data = new_data

    # Define getters for header variables
    @property
    def time(self) -> np.float32:
        """Get the simulation time of the spectra file.

        Returns
        -------
        np.float32
            The time in the spectra file
        """
        return self.__time

    @property
    def n_prp(self) -> int | list[int]:
        """Get n_prp.

        Returns
        -------
        int | list[int]
            The value(s) of n_prp
        """
        return self.__n_prp

    @property
    def n_prl(self) -> int | list[int]:
        """Get n_prl.

        Returns
        -------
        int | list[int]
            The value(s) of n_prl
        """
        return self.__n_prl

    @property
    def max_w_prp(self) -> float | list[float]:
        """Get max_w_prp.

        Returns
        -------
        float | list[float]
            The value(s) of max_w_prp
        """
        return self.__max_w_prp

    @property
    def max_w_prl(self) -> float | list[float]:
        """Get max_w_prl.

        Returns
        -------
        float | list[float]
            The value(s) of max_w_prl
        """
        return self.__max_w_prl

    @property
    def num_ions(self) -> int:
        """Get num_ions.

        Returns
        -------
        int
            The value of num_ion
        """
        return self.__num_ions

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
        if self.__file_type != "spec":
            msg = "Reducing is only supported for .spec files."
            raise RuntimeError(msg)

        # Type narrowing
        assert isinstance(self.__n_prl, int)  # noqa: S101
        assert isinstance(self.__n_prp, int)  # noqa: S101
        assert isinstance(self.__max_w_prl, float)  # noqa: S101
        assert isinstance(self.__max_w_prp, float)  # noqa: S101

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
