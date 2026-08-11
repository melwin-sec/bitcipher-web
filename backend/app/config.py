import os


class Config:
    """
    BitCipher backend configuration.

    All values are overridable via environment variables so Render/local
    .env files control behavior -- nothing security-sensitive should be
    hardcoded here.
    """

    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        # Fail loudly in any real deployment rather than silently running
        # with a predictable/missing key. Fine to leave unset only for
        # `flask shell` / one-off local scripts that don't need it.
        if os.getenv("FLASK_ENV") == "production" or os.getenv("RENDER"):
            raise RuntimeError(
                "SECRET_KEY environment variable must be set in production."
            )
        SECRET_KEY = "dev-only-insecure-key-do-not-deploy"

    # CORS: default to closed rather than "*". Set CORS_ORIGINS explicitly
    # in every environment (e.g. https://bitcipher.vercel.app). Comma-
    # separate multiple origins if needed.
    _raw_origins = os.getenv("CORS_ORIGINS", "")
    CORS_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()] or []

    # scrypt KDF parameters. OWASP's current minimum baseline is
    # N=2^17 (131072), r=8, p=1. 8192 (2^13) is well below that and
    # should only be used for local/dev speed, never production.
    SCRYPT_N = int(os.getenv("SCRYPT_N", 2**17))
    SCRYPT_R = int(os.getenv("SCRYPT_R", 8))
    SCRYPT_P = int(os.getenv("SCRYPT_P", 1))

    MAX_TEXT_BYTES = int(os.getenv("MAX_TEXT_BYTES", 64 * 1024))

    # Password generator bounds
    PASSWORD_MIN_LENGTH = 4
    PASSWORD_MAX_LENGTH = 64  # widened slightly from 16, still bounded
