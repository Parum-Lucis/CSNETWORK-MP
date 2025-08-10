from models.peer import Profile
from storage.peer_directory import update_peer
from utils.printer import verbose_log
from utils.base64_utils import decode_base64_to_image
import os

def handle_profile(msg: dict, addr):
    """
    Handles a PROFILE message broadcasted by another peer.

    Args:
        msg (dict): A parsed LSNP message containing peer profile info.
        addr (tuple): The sender's network address (IP, port).

    Note: AI-generated
    """

    profile = Profile.from_message(msg, addr)
    update_peer(profile.user_id, profile)

    if profile.avatar_type and profile.avatar_data:
        decode_base64_to_image(profile.avatar_data, f"{profile.user_id}_avatar.{profile.avatar_type}")

    verbose_log("INFO", f"Updated peer profile: {profile.user_id} from {addr}")
