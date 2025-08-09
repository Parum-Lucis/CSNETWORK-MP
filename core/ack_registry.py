
pending_acks = {}

def register_ack(message_id: str, on_ack: callable):
    """
    Registers a callback to run when an ACK for the given message ID is received.
    """
    pending_acks[message_id] = on_ack

def resolve_ack(message_id: str):
    """
    Executes the callback associated with a message ID if it exists.
    """
    if message_id in pending_acks:
        callback = pending_acks.pop(message_id)
        callback()
        return True
    return False
