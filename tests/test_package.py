import importlib.metadata

import pegasustools as pt


def test_version():
    assert importlib.metadata.version("pegasustools") == pt.__version__
