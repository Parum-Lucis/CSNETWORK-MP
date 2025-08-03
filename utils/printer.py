import os
import config

def verbose_log(prefix: str, message: str):
    """
        Prints debug/log messages only if VERBOSE mode is enabled.

        Args:
            prefix (str): A label of the message to be printed.
            message (str): The message body to display.
    """
    if config.VERBOSE:
        print(prefix + " " + message)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')