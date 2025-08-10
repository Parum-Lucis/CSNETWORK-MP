import threading
import time
from models.peer import Profile
from core.udp_broadcast import UDPListener
from utils.printer import verbose_log
from config import BROADCAST_INTERVAL

def start_broadcast(local_profile: Profile, udp_sender: UDPListener):
    """
    Starts a background thread that periodically (based on BROADCAST_INTERVAL) broadcast messages to the network.

    Args:
        local_profile (Profile): the local peer's profile data.
        udp_sender (UDPListener): the UDPListener object used for broadcasting.
    """
    def loop():
        while True:
            msg = build_profile_message(local_profile)
            udp_sender.send_broadcast(msg)
            verbose_log("BROADCAST", "Sent PROFILE broadcast")
            time.sleep(BROADCAST_INTERVAL)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()

def build_profile_message(profile: Profile) -> str:
    """
    Formats a LSNP Profile message from a Profile Object based on the LSNP standard
    Required fields:
        TYPE: PROFILE
        USER_ID
        DISPLAY_NAME
        STATUS

    Optional fields:
        AVATAR_TYPE
        AVATAR_DATA

    Args:
        profile (Profile): The local peer's Profile instance.

    Returns:
        str: A formatted string ready to be sent via UDP broadcast.
    """
    lines = [
        "TYPE: PROFILE",
        f"USER_ID: {profile.user_id}",
        f"DISPLAY_NAME: {profile.display_name}",
        f"STATUS: {profile.status}"
    ]
    if profile.avatar_type:
        lines.append(f"AVATAR_TYPE: {profile.avatar_type}")
    if profile.avatar_data:
        lines.append(f"AVATAR_DATA: {profile.avatar_data}")

    return "\n".join(lines) + "\n\n"