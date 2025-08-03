from core.udp_broadcast import UDPListener

_udp_instance = None

def get_udp_listener() -> UDPListener:
    global _udp_instance
    if _udp_instance is None:
        _udp_instance = UDPListener()
    return _udp_instance
