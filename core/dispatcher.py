from handlers.ack_handler import handle_ack
from handlers.file_handler import handle_file
from handlers.profile_handler import handle_profile
from handlers.post_handler import handle_post
from handlers.direct_message_handler import handle_dm
from utils.printer import verbose_log

def parse_message(message: str) -> dict:
    """
    Parses a raw LSNP key-value message string into a dictionary with the format KEY: VALUE.
    Args:
        message (str): A raw LSNP key-valye message received over the network.

    Returns:
        dict: dictionary where each key-value pair in the message is extracted
    """
    lines = message.strip().split("\n")
    msg_dict = {}
    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            msg_dict[key.strip()] = value.strip()
    return msg_dict

class Dispatcher:
    """
    class responsible for routing parsed LSNP messages to the appropriate handler based on the 'TYPE' field.

    Supported message types:
        Profile through handle_profile()
        POST through handle_post()
        DM through handle_dm()

    For Messages without a recognized TYPE, it will be logged as a warning!
    """

    def __init__(self, listener):
        """
        listener: the UDP listener object, so handlers can send messages back
        """
        self.listener = listener

    def handle(self, raw_message: str, addr):
        """
            Entry point for handling all incoming raw UDP messages.
            Functions
                Logs the raw message if VERBOSE = TRUE
                Parses the message into a dictionary
                Determines message TYPE
                Routes the message to the correct handler function

            Args:
                raw_message (str): the raw LSNP message received over the network.
                addr (tuple): address of the sender with (IP, port).
        """
        verbose_log("RECV <", raw_message)
        msg = parse_message(raw_message)
        msg_type = msg.get("TYPE")

        if msg_type == "PROFILE":
            handle_profile(msg, addr)
        elif msg_type == "POST":
            handle_post(msg, addr)
        elif msg_type == "DM":
            handle_dm(msg, addr)
        elif msg_type == "ACK":
            handle_ack(msg, addr)
        elif msg_type in ("FILE_OFFER", "FILE_CHUNK", "FILE_RECEIVED"):
            handle_file(msg, addr, self.listener)
        else:
            verbose_log("WARN", f"Unknown TYPE: {msg_type}")

