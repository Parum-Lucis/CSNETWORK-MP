from core.token_validator import parse_token, revoke_token
from utils.printer import verbose_log


# Only these scopes are allowed to be revoked
ALLOWED_REVOKE_SCOPES = {"dm", "game", "file"}  # two-way exchanges only


def send_revoke(udp_listener, from_profile, token, target_ip=None):
    """
    Sends a REVOKE message to a peer or broadcasts it, but only for allowed scopes.
    """
    user_id, expiry, scope = parse_token(token)

    if scope not in ALLOWED_REVOKE_SCOPES:
        verbose_log("WARN", f"Revocation not allowed for scope '{scope}'")
        return False

    revoke_msg = {
        "TYPE": "REVOKE",
        "FROM": from_profile.user_id,
        "TOKEN": token
    }
    msg_str = "\n".join(f"{k}: {v}" for k, v in revoke_msg.items()) + "\n\n"

    verbose_log("SEND >", msg_str)
    if target_ip:
        udp_listener.send_unicast(msg_str, target_ip)
    else:
        udp_listener.send_broadcast(msg_str)
    return True
