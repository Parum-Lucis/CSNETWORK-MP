import time

def current_unix_time() -> int:
    """
    Returns the current time as a UNIX timestamp (seconds since epoch).

    Returns:
        int: Current time in seconds
    """
    return int(time.time())

def wait_for_enter():
    input("\n🔙 Press Enter to return to the main menu...")