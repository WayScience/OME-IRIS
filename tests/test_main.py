"""
Tests for the main module.
"""

from OME_IRIS.main import show_message


def test_show_message(my_data: str) -> None:
    """
    Test the show_message function.
    """

    # Test default message
    result = show_message()
    assert result.shape == (1, 1)
    assert result.iloc[0, 0] == "Hello, world!"

    result = show_message(my_data)
    assert result.shape == (1, 1)
    assert result.iloc[0, 0] == my_data
