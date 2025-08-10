import socket

def get_local_ip() -> str:
    """
    Gets the local IP address used to connect to the network.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

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