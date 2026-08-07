#!/usr/bin/env python3
"""Point d'entrée CLI Epic Events."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from epic_events.cli import cli
from epic_events.logging_sentry import capture_unexpected, init_sentry


def main() -> None:
    init_sentry()
    try:
        cli(standalone_mode=True)
    except SystemExit:
        raise
    except Exception as exc:
        capture_unexpected(exc)
        raise


if __name__ == "__main__":
    main()
