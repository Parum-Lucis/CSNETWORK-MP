import os
import config

# Global session log storage
VERBOSE_LOGS = []
NOTIFICATIONS = []

def verbose_log(prefix: str, message: str):
    """
    Logs debug messages to the session storage and prints if VERBOSE is enabled.

    Args:
        prefix (str): Label of the message.
        message (str): Message content.
    """
    log_entry = f"{prefix} {message}"
    VERBOSE_LOGS.append(log_entry)

def get_verbose_logs():
    """
    Returns all stored verbose log entries.
    """
    return VERBOSE_LOGS

def clear_verbose_logs():
    """
    Clears the stored verbose logs.
    """
    VERBOSE_LOGS.clear()

def notif_log(message: str):
    """
    Logs debug messages to the session storage and prints if VERBOSE is enabled.

    Args:
        message (str): Message content.
    """
    log_entry = f"{message}"
    NOTIFICATIONS.append(log_entry)

def get_notif():
    """
    Returns all stored verbose log entries.
    """
    return NOTIFICATIONS

def clear_notif():
    """
    Clears the stored verbose logs.
    """
    NOTIFICATIONS.clear()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')