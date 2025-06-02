"""Copyright (c) 2025 Robert Caddy. All rights reserved.

PegasusTools: Analysis package for the Pegasus PIC code.
"""

# Import all relevant modules into the pegasustools namespacess
from pegasustools.loading_nbf import PegasusNBFData
from pegasustools.loading_spectra import PegasusSpectralData
from pegasustools.loading_tracks import (
    PegasusTrack,
    collate_tracks_from_ascii,
    collate_tracks_from_binary,
)

# Set version
from ._version import version as __version__

# Setup what gets imported with import *
__all__ = [
    "PegasusNBFData",
    "PegasusSpectralData",
    "PegasusTrack",
    "__version__",
    "collate_tracks_from_ascii",
    "collate_tracks_from_binary",
]
