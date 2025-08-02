import os
import base64
import mimetypes
import subprocess
import sys
from config import MAX_AVATAR_SIZE

def encode_image_to_base64(filepath: str) -> tuple[str, str] | None:
    """
    Reads an image file and returns its MIME type and base64-encoded string.

    Args:
        filepath (str): Path to the image file.

    Returns:
        tuple: (mime_type, base64_encoded_string), or None if error

    Note: AI-generated
    """
    if not os.path.exists(filepath):
        print(f"[Error] Avatar file does not exist: {filepath}")
        return None

    size = os.path.getsize(filepath)
    if size > MAX_AVATAR_SIZE:
        print(f"[Error] Avatar image too large ({size} bytes). Max is {MAX_AVATAR_SIZE} bytes.")
        return None

    mime_type, _ = mimetypes.guess_type(filepath)
    try:
        with open(filepath, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return mime_type, encoded
    except Exception as e:
        print(f"[Error] Failed to encode avatar: {e}")
        return None


def decode_base64_to_image(base64_str: str, output_path: str):
    """
    Decodes base64 string and writes it as an image file.

    Args:
        base64_str (str): The base64-encoded image data.
        output_path (str): Path to save the decoded image.

    Note: AI-generated
    """
    try:
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(base64_str))
    except Exception as e:
        print(f"[Error] Failed to decode avatar: {e}")

def preview_image(path: str):
    """
    Opens an image using the system's default viewer.

    Args:
        path (str): Path to the image file.

    Note: AI-generated
    """
    try:
        if sys.platform.startswith('darwin'):
            subprocess.run(['open', path])
        elif os.name == 'nt':
            os.startfile(path)
        elif os.name == 'posix':
            subprocess.run(['xdg-open', path])
        else:
            print("[Error] Preview not supported on this OS.")
    except Exception as e:
        print(f"[Error] Could not preview image: {e}")