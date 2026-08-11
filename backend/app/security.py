"""
BitCipher security middleware.

Provides:
- Flask-Limiter rate limiting (per-IP, per-endpoint)
- Security response headers (CSP, HSTS, X-Frame-Options, etc.)
- A small helper to register everything on the app factory.

Usage in app/__init__.py:

    from .security import init_security

    def create_app():
        app = Flask(__name__)
        ...
        init_security(app)
        ...
        return app
"""

import os
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Shared limiter instance. Imported by routes.py to apply
# per-route limits with @limiter.limit("...").
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.getenv("RATE_LIMIT_STORAGE_URI", "memory://"),
)

# Endpoints that run scrypt are expensive -- clamp them harder than
# the default. Import these constants from routes.py.
ENCRYPT_DECRYPT_LIMIT = "10 per minute"
PASSWORD_GEN_LIMIT = "30 per minute"
WARMUP_LIMIT = "60 per minute"


def _security_headers(response):
    """Attach standard security headers to every response."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = (
        "geolocation=(), microphone=(), camera=()"
    )
    # API-only backend, so a strict CSP is safe -- no HTML is served.
    response.headers["Content-Security-Policy"] = "default-src 'none'"
    # Only meaningful over HTTPS (Render terminates TLS in front of us),
    # but harmless to always set.
    response.headers["Strict-Transport-Security"] = (
        "max-age=63072000; includeSubDomains; preload"
    )
    return response


def _reject_oversized_requests():
    """Hard cap request body size before it ever reaches a route.

    Defends against large-payload DoS against the scrypt-backed
    encrypt/decrypt endpoints. 256 KB is generous headroom above the
    64 KB plaintext limit enforced in crypto.py.
    """
    max_bytes = 256 * 1024
    content_length = request.content_length
    if content_length is not None and content_length > max_bytes:
        return jsonify({"error": "Request body too large"}), 413


def init_security(app: Flask) -> None:
    """Wire rate limiting, headers, and request-size guards onto app."""
    limiter.init_app(app)

    app.before_request(_reject_oversized_requests)
    app.after_request(_security_headers)

    @app.errorhandler(429)
    def _rate_limited(_e):
        return jsonify({"error": "Too many requests. Please slow down."}), 429
