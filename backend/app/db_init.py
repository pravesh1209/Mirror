"""Initialize the database schema. Idempotent.

Usage:
    python -m app.db_init
"""
from __future__ import annotations

import asyncio
import logging

from .db import init_models

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("mirror.db_init")


async def main() -> None:
    await init_models()
    log.info("Schema created/verified.")


if __name__ == "__main__":
    asyncio.run(main())
