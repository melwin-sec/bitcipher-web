import base64
import binascii
import secrets
import string
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.fernet import Fernet, InvalidToken

from .config import Config


SALT_SIZE = 16
MAX_TEXT_BYTES = 64 * 1024


class CryptoError(ValueError):
    """Raised when encrypted input cannot be safely decoded or decrypted."""


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=Config.SCRYPT_N,
        r=Config.SCRYPT_R,
        p=Config.SCRYPT_P,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def encrypt_text(text: str, password: str):
    if not text or not password:
        raise CryptoError("Text and password are required")
    if len(text.encode("utf-8")) > MAX_TEXT_BYTES:
        raise CryptoError("Text is too large")

    salt = secrets.token_bytes(SALT_SIZE)
    key = derive_key(password, salt)
    token = Fernet(key).encrypt(text.encode("utf-8"))
    encoded = base64.b64encode(salt + token).decode()

    return {
        "encoded": encoded,
        # Backward-compatible alias for older frontend code paths.
        "ciphertext": encoded,
    }


def decrypt_text(encoded: str, password: str):
    if not encoded or not password:
        raise CryptoError("Encoded text and password are required")

    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise CryptoError("Invalid encoded payload") from exc

    if len(raw) <= SALT_SIZE:
        raise CryptoError("Invalid encoded payload")

    salt = raw[:SALT_SIZE]
    token = raw[SALT_SIZE:]
    key = derive_key(password, salt)

    try:
        return Fernet(key).decrypt(token).decode("utf-8")
    except (InvalidToken, UnicodeDecodeError) as exc:
        raise CryptoError("Invalid password or encrypted message") from exc


def generate_password(length: int = 16, include_symbols: bool = True):
    safe_length = max(Config.PASSWORD_MIN_LENGTH, min(Config.PASSWORD_MAX_LENGTH, int(length)))
    alphabet = string.ascii_letters + string.digits
    if include_symbols:
        alphabet += "!@#$%^&*()"
    return "".join(secrets.choice(alphabet) for _ in range(safe_length))


def warmup_crypto() -> bool:
    sample_password = "bitcipher-warmup-password"
    sample_text = "bitcipher warmup"
    encrypted = encrypt_text(sample_text, sample_password)["encoded"]
    return decrypt_text(encrypted, sample_password) == sample_text
