import time
from utils.printer import verbose_log

# Stores revoked tokens with their expiry time
# Key: token string
# Value: expiry UNIX timestamp
revoked_tokens = {}


def parse_token(token: str):
    """
    Parses an LSNP token string into components.

    Args:
        token (str): The raw token string to parse.

    Returns:
        tuple: (user_id, expiry, scope)
               Returns (None, None, None) if token is invalid.
    """
    try:
        user_id, expiry, scope = token.split("|")
        return user_id, int(expiry), scope
    except Exception:
        return None, None, None


def validate_token(token: str, expected_scope: str) -> bool:
    """
    Validates a given LSNP token based on:
        - Format: USER_ID|UNIX_EXPIRY|SCOPE
        - Scope matches the expected scope
        - Token has not expired
        - Token has not been revoked

    Args:
        token (str): The token to validate.
        expected_scope (str): Required scope (e.g., 'chat', 'file', 'group').

    Returns:
        bool: True if token is valid, False otherwise.
    """
    user_id, expiry, scope = parse_token(token)
    current_time = int(time.time())

    # Check if token components are valid
    if not all([user_id, expiry, scope]):
        verbose_log("DROP!", f"Malformed token: {token}")
        return False

    # Scope mismatch
    if scope != expected_scope:
        verbose_log("DROP!", f"Scope mismatch: got '{scope}', expected '{expected_scope}'")
        return False

    # Token expired
    if current_time > expiry:
        verbose_log("DROP!", f"Expired token for {user_id} (expired at {expiry})")
        return False

    # Token revoked
    if token in revoked_tokens:
        verbose_log("DROP!", f"Revoked token used by {user_id}")
        return False

    return True


def revoke_token(token):
    """
    Adds a token to the revocation list until it expires.

    Args:
        token (str): The token string to revoke.
    """
    _, expiry, _ = parse_token(token)
    if expiry:
        revoked_tokens[token] = expiry


def cleanup_revoked_tokens():
    """
    Removes expired tokens from the revocation list.
    Should be called periodically in the main loop.
    """
    now = int(time.time())
    for t, exp in list(revoked_tokens.items()):
        if exp < now:
            del revoked_tokens[t]