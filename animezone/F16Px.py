import base64
import json
from utils import python_aesgcm
import yaml


# --- FILEMOON ---


def b64url_decode(value: str) -> bytes:
    # base64url -> base64
    value = value.replace("-", "+").replace("_", "/")
    padding = (-len(value)) % 4
    if padding:
        value += "=" * padding
    return base64.b64decode(value)


def join_key_parts(parts) -> bytes:
    return b"".join(b64url_decode(p) for p in parts)


def filemoon(payload):

    pb = yaml.load(payload, Loader=yaml.BaseLoader)
    if not pb:
        return None

    iv = b64url_decode(pb["iv"])  # nonce
    key = join_key_parts(pb["key_parts"])  # AES key
    payload = b64url_decode(pb["payload"])  # ciphertext + tag
    cipher = python_aesgcm.new(key)
    decrypted = cipher.open(iv, payload)  # AAD = '' like ResolveURL

    if decrypted is None:
        return None

    decrypted_json = json.loads(decrypted.decode("utf-8", "ignore"))
    sources = decrypted_json.get("sources") or []
    if not sources:
        return None

    best = sources[0].get("url")
    if not best:
        return None
    return best