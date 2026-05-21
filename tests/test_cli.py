"""
Tests for the cli module.
"""

import subprocess


def test_show_message_cli(my_data: str) -> None:
    """
    Test the show_message function from the CLI.
    """

    output = subprocess.run(
        ["uv", "run", "OME-IRIS", "show_message", f"--message='Hello terminal!'"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Hello terminal!" in str(output.stdout)
