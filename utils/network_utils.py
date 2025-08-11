import socket
import sys

def get_local_ip():
    """Return the IP from args if provided, otherwise detect automatically."""
    # If user passed an IP as the first argument after the script name
    if len(sys.argv) > 1:
        return sys.argv[1]

    # Otherwise, detect automatically
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def get_broadcast_ip() -> str:
    """
    Attempts to compute the local subnet's senders IP based on the current IP.

    Returns:
        str: A senders IP address like '192.168.1.255'
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()

        ip_parts = local_ip.split('.')
        ip_parts[-1] = '255'
        return '.'.join(ip_parts)

    except Exception:
        return '255.255.255.255'


def verify_sender_ip(msg: dict, addr: tuple) -> bool:
    """
    Checks if the IP in the FROM field matches the actual UDP sender IP.

    Args:
        msg (dict): Parsed LSNP message.
        addr (tuple): (ip, port) from UDP socket.

    Returns:
        bool: True if IP matches, False if spoof detected.
    """
    from_field = msg.get("FROM", "")
    if "@" not in from_field:
        return False  # malformed FROM
    declared_ip = from_field.split("@")[1]
    actual_ip = addr[0]
    return declared_ip == actual_ip