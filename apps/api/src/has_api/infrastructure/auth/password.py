"""Password hashing with bcrypt (direct, no passlib wrapper).

passlib 1.7.4 is incompatible with bcrypt >= 4.1 (it reads
``bcrypt.__about__.__version__`` which no longer exists), so we use
bcrypt directly. Hashes are stored in the standard Modular Crypt Format
(``$2b$...``) — the same format passlib produced — so existing users keep working.
"""

import bcrypt


def hash_password(plain: str) -> str:
    """Return bcrypt hash of the plain-text password."""
    hashed = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False
