from models.peer import Profile
from storage.peer_directory import update_peer
from utils.printer import verbose_log

def handle_profile(msg: dict, addr):
    """
    Handles a PROFILE message broadcasted by another peer.

    Args:
        msg (dict): A parsed LSNP message containing peer profile info.
        addr (tuple): The sender's network address.
    """

    profile = Profile.from_message(msg, addr)
    update_peer(profile.user_id, profile)
    print(str(profile))
    verbose_log("INFO", f"Updated peer profile: {profile.user_id} from {addr}")
