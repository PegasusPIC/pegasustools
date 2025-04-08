"""Copyright (c) 2025 Robert Caddy. All rights reserved.

pegasustools: Analysis package for the Pegasus PIC code.
"""

# Import all relevant modules into the pegasustools namespacess
from pegasustools.loading_nbf import PegasusNBFData

# Set version
from ._version import version as __version__

# Setup what gets imported with import *
__all__ = [
    "PegasusNBFData",
    "__version__",
]
