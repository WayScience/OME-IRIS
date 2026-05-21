"""
An example module for a Python research software project.
"""

import pandas as pd


def show_message(message: str = "Hello, world!") -> pd.DataFrame:
    """
    A simple function that returns a message
    from within a Pandas DataFrame.

    Args:
        message (str):
            The message to print.
            Defaults to 'Hello, world!'.

    Returns:
        pd.DataFrame:
            A DataFrame containing the message.
    """

    return pd.DataFrame({"message": [message]})
