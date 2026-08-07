"""Création et décodage des jetons JWT."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from epic_events.config import get_jwt_settings


class TokenError(Exception):
    """Jeton invalide, altéré ou expiré."""


def create_access_token(*, employee_id: int, email: str, department: str) -> str:
    """Émet un JWT signé (HS256) avec date d'expiration."""
    settings = get_jwt_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(employee_id),
        "email": email,
        "department": department,
        "iat": now,
        "exp": now + timedelta(hours=settings.expire_hours),
    }
    return jwt.encode(payload, settings.secret, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Décode et valide un JWT. Lève TokenError si expiré ou invalide."""
    settings = get_jwt_settings()
    try:
        return jwt.decode(
            token,
            settings.secret,
            algorithms=[settings.algorithm],
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenError(
            "Session expirée. Reconnectez-vous avec la commande login."
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("Jeton invalide. Reconnectez-vous.") from exc
