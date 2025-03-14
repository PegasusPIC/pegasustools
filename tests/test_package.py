import importlib.metadata

import pegasustools as m


def test_version():
    assert importlib.metadata.version("pegasustools") == m.__version__
