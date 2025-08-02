from config import VERBOSE

def verbose_log(prefix: str, message: str):
    """
        Prints debug/log messages only if VERBOSE mode is enabled.

        Args:
            prefix (str): A label of the message to be printed.
            message (str): The message body to display.
    """
    if VERBOSE:
        print(prefix + " " + message)
