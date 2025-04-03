"""Copyright (c) 2025 Robert Caddy. All rights reserved.

PegasusTools: Analysis package for the Pegasus PIC code.
"""

# Import all relevant modules into the pegasustools namespace
from pegasustools.loading_data import load_file
from pegasustools.loading_nbf import PegasusNBFData
from pegasustools.loading_spectra import (
    PegasusSpectralData,
    og_spectra_reader,
)

# Set version
from ._version import version as __version__

# Setup what gets imported with import *
__all__ = [
    "PegasusNBFData",
    "PegasusSpectralData",
    "__version__",
    "load_file",
    "og_spectra_reader",
]
