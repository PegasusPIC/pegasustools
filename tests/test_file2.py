import pegasustools as pt


def test_times_6() -> None:
    """Verify that pt.times_6 is correct."""
    test_var: int = 4
    assert pt.times_6(test_var) == 6 * test_var
