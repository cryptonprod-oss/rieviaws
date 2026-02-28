from dataclasses import dataclass
import os
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: set[int]
    timezone: ZoneInfo


def _parse_admin_ids(raw: str) -> set[int]:
    if not raw:
        return set()

    parsed: set[int] = set()
    for chunk in raw.split(","):
        value = chunk.strip()
        if not value:
            continue
        parsed.add(int(value))
    return parsed


def load_settings() -> Settings:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise ValueError("BOT_TOKEN is required in .env")

    admin_ids = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))
    if not admin_ids:
        raise ValueError("ADMIN_IDS is required in .env and must contain at least one ID")

    timezone_name = os.getenv("TIMEZONE", "UTC").strip() or "UTC"
    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Invalid TIMEZONE: {timezone_name}") from exc

    return Settings(bot_token=bot_token, admin_ids=admin_ids, timezone=timezone)
