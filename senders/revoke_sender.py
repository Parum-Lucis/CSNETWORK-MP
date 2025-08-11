from utils.token_utils import revoke_token
from utils.printer import verbose_log


def send_revoke(udp_listener, from_profile, token, target_ip=None):
    """
    Sends a REVOKE message to the network.

    Args:
        udp_listener: Network listener with send_broadcast / send_unicast.
        from_profile: Profile of the local user.
        token (str): The token to revoke.
        target_ip (str, optional): If given, send REVOKE to this peer only.
    """
    revoke_msg = {
        "TYPE": "REVOKE",
        "TOKEN": token
    }
    msg_str = "\n".join(f"{k}: {v}" for k, v in revoke_msg.items()) + "\n\n"

    # Send either as broadcast or unicast
    if target_ip:
        udp_listener.send_unicast(msg_str, target_ip)
        verbose_log("SEND >", f"REVOKE to {target_ip}: TOKEN: {token}")
    else:
        udp_listener.send_broadcast(msg_str)
        verbose_log("SEND >", f"REVOKE broadcast: TOKEN: {token}")

    # Revoke locally as well
    revoke_token(token)