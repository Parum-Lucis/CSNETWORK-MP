import socket
import threading
from config import BUFFER_SIZE
from utils.network_utils import get_broadcast_ip

class UDPListener:
    """
        A UDP communication wrapper for LSNP peers.
    """
    def __init__(self, port=50999):
        """
           Initializes the UDP socket based on the senders and reuse settings on all network interfaces' ports.

           Args:
               port (int): The UDP port to listen on. Default is 50999.
        """
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind(('', port))

    def start(self, on_message_callback):
        """
        Starts a background thread to listen for incoming UDP messages.

        Args:
            on_message_callback (function): function that processes the received message.

        Notes:
            Runs in a separate daemon thread whatever that is
        """
        def listener():
            while True:
                    try:
                        data, addr = self.sock.recvfrom(BUFFER_SIZE)
                        message = data.decode('utf-8'  , errors='ignore')
                        on_message_callback(message, addr)
                    except Exception as e:
                        print(f"[Error] UDP receive failed: {e}")
        thread = threading.Thread(target=listener)
        thread.start()

    def send_broadcast(self, message: str):
        """
        UDP senders to all peers on the local network.

        Args:
            message (str): The LSNP-formatted message to send; TODO change to actual receiver
        """
        broadcast_ip = get_broadcast_ip()
        self.sock.sendto(message.encode('utf-8'), (broadcast_ip, self.port))

    def send_unicast(self, message, ip: str):
        """
        Sends a message via UDP unicast directly to a specific peer's IP.

        Args:
            message (str): The LSNP-formatted message to send.
            ip (str): The IP address of the target peer; TODO change to actual receiver
        """
        self.sock.sendto(message.encode('utf-8'), (ip, self.port))