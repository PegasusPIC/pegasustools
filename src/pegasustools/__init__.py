"""
Copyright (c) 2025 Robert Caddy. All rights reserved.

pegasustools: Analysis package for the Pegasus PIC code.
"""

from ._version import version as __version__

__all__ = ["__version__", "times_2", "times_6"]

# Import all relevant modules into the pegasustools namespace
from pegasustools.file1 import times_2
from pegasustools.file2 import times_6
