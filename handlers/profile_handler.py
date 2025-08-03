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

    if profile.avatar_data and profile.avatar_type and profile.avatar_type.startswith("image/"):
        os.makedirs("avatars", exist_ok=True)  # Create directory if it doesn't exist
        file_ext = profile.avatar_type.split("/")[-1]  # e.g., "png", "jpeg"
        output_path = f"avatars/{profile.user_id}.{file_ext}"
        decode_base64_to_image(profile.avatar_data, output_path)
        verbose_log("INFO", f"Saved avatar for {profile.user_id} to {output_path}")

    verbose_log("INFO", f"Updated peer profile: {profile.user_id} from {addr}")
