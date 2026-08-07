#!/usr/bin/env python3
"""Crée les tables PostgreSQL et les départements de référence."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from epic_events.db import check_connection, init_db


def main() -> None:
    print(check_connection())
    init_db()
    print("Tables et départements initialisés.")


if __name__ == "__main__":
    main()
