"""Hachage et vérification des mots de passe (Argon2id)."""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

# Instance unique : salt aléatoire inclus dans chaque hash Argon2
_hasher = PasswordHasher()


def hash_password(plain_password: str) -> str:
    """Retourne un hash Argon2id (salt + paramètres inclus dans la chaîne)."""
    if not plain_password:
        raise ValueError("Le mot de passe ne peut pas être vide.")
    return _hasher.hash(plain_password)


def verify_password(password_hash: str, plain_password: str) -> bool:
    """Vérifie un mot de passe en clair contre le hash stocké."""
    try:
        return _hasher.verify(password_hash, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
