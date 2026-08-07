"""Initialisation et helpers Sentry (journalisation)."""

from __future__ import annotations

import os
from typing import Any

import sentry_sdk

_initialized = False


def init_sentry() -> bool:
    """Initialise Sentry si SENTRY_DSN est défini. Retourne True si actif."""
    global _initialized
    if _initialized:
        return bool(sentry_sdk.is_initialized())

    dsn = os.getenv("SENTRY_DSN", "").strip()
    _initialized = True
    if not dsn:
        return False

    sentry_sdk.init(
        dsn=dsn,
        send_default_pii=False,
        traces_sample_rate=0.0,
        environment=os.getenv("SENTRY_ENVIRONMENT", "development"),
    )
    return True


def capture_unexpected(exc: BaseException) -> None:
    """Envoie une exception inattendue à Sentry (no-op si désactivé)."""
    if sentry_sdk.is_initialized():
        sentry_sdk.capture_exception(exc)


def log_event(message: str, *, level: str = "info", **context: Any) -> None:
    """Journalise un événement métier (création collab, signature, etc.)."""
    if not sentry_sdk.is_initialized():
        return

    with sentry_sdk.new_scope() as scope:
        for key, value in context.items():
            scope.set_extra(key, value)
        sentry_sdk.capture_message(message, level=level)
