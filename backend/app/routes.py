from flask import Blueprint, request, jsonify
from .crypto import encrypt_text, decrypt_text, generate_password, warmup_crypto
from .config import Config
from .security import (
    limiter,
    ENCRYPT_DECRYPT_LIMIT,
    PASSWORD_GEN_LIMIT,
    WARMUP_LIMIT,
)

api = Blueprint("api", __name__)


def _bad_request(message):
    return jsonify({"error": message}), 400


@api.route("/encrypt", methods=["POST"])
@limiter.limit(ENCRYPT_DECRYPT_LIMIT)
def encrypt():
    data = request.get_json(silent=True) or {}
    plaintext = data.get("plaintext")
    password = data.get("password")

    if not plaintext or not password:
        return _bad_request("Text and password are required")
    if not isinstance(plaintext, str) or not isinstance(password, str):
        return _bad_request("Text and password must be strings")
    if len(plaintext.encode("utf-8")) > Config.MAX_TEXT_BYTES:
        return _bad_request(
            f"Text exceeds maximum size of {Config.MAX_TEXT_BYTES} bytes"
        )
    if len(password) < 8:
        return _bad_request("Password must be at least 8 characters")

    try:
        result = encrypt_text(plaintext, password)
    except Exception:
        return jsonify({"error": "Encryption failed"}), 500

    return jsonify(result)


@api.route("/decrypt", methods=["POST"])
@limiter.limit(ENCRYPT_DECRYPT_LIMIT)
def decrypt():
    data = request.get_json(silent=True) or {}
    encoded = data.get("encoded")
    password = data.get("password")

    if not encoded or not password:
        return _bad_request("Encoded text and password are required")
    if not isinstance(encoded, str) or not isinstance(password, str):
        return _bad_request("Encoded text and password must be strings")

    try:
        plaintext = decrypt_text(encoded, password)
    except Exception:
       return jsonify({"success": False, "error": "Invalid password or encrypted text"})

    return jsonify({"plaintext": plaintext})


@api.route("/generate-password", methods=["POST"])
@limiter.limit(PASSWORD_GEN_LIMIT)
def generate_password_route():
    data = request.get_json(silent=True) or {}

    raw_length = data.get("length", 12)
    try:
        length = int(raw_length)
    except (TypeError, ValueError):
        return _bad_request("length must be a number")

    length = max(Config.PASSWORD_MIN_LENGTH, min(Config.PASSWORD_MAX_LENGTH, length))

    # Coerce booleans safely -- avoid `bool("false") == True` footgun.
    def _as_bool(value, default=True):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() not in ("false", "0", "no", "")
        return default

    include_symbols = _as_bool(data.get("includeSymbols", True))

    # NOTE: the real generate_password() currently only accepts
    # `length` and `include_symbols`. Do not pass includeNumbers /
    # includeUppercase until crypto.py is deliberately extended to
    # support them (and the frontend is updated to match).
    password = generate_password(
        length=length,
        include_symbols=include_symbols,
    )
    return jsonify({"password": password, "length": length})


@api.route("/warmup", methods=["GET"])
@limiter.limit(WARMUP_LIMIT)
def warmup():
    warmup_crypto()
    return jsonify({"ready": True})
