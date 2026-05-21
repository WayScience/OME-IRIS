"""
CLI for OME_IRIS
"""

import fire

from OME_IRIS.main import show_message


class OME_IRISCLI:
    def show_message(
        self,
        message: str = "Hello, world!",
    ) -> str:
        """
        CLI interface for show_message.

        Args:
            message (str):
                The message to print.
                Defaults to 'Hello, world!'.

        Returns:
            pd.DataFrame:
                A DataFrame containing the message.
        """

        # prints the message to screen
        print(show_message(message=message))


def trigger() -> None:
    """
    Trigger the CLI to run.
    """
    fire.Fire(OME_IRISCLI)
