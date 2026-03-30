from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

from config import get_settings
from storage import MongoDebateStore


load_dotenv(Path(__file__).with_name(".env"))


async def main() -> int:
    settings = get_settings()
    if not settings.mongodb_uri:
        print("MongoDB startup check failed: MONGODB_URI is missing.", file=sys.stderr)
        return 1

    store = MongoDebateStore(
        settings.mongodb_uri,
        settings.mongodb_db_name,
        timeout_ms=settings.mongodb_timeout_ms,
    )
    try:
        await store.ensure_indexes()
    except Exception as exc:
        print(f"MongoDB startup check failed: {exc}", file=sys.stderr)
        return 1
    finally:
        await store.close()

    print("MongoDB startup check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
