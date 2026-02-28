from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import aiosqlite


@dataclass(frozen=True)
class ReviewLogRecord:
    admin_user_id: int
    username: str
    pay_date: str
    order_no: str
    rating: int
    review_text: str


async def init_db(db_path: str) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS counter (
                id INTEGER PRIMARY KEY CHECK (id=1),
                last_order INTEGER NOT NULL
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                admin_user_id INTEGER,
                username TEXT,
                pay_date TEXT,
                order_no TEXT,
                rating INTEGER,
                review_text TEXT
            )
            """
        )
        await db.execute(
            "INSERT OR IGNORE INTO counter (id, last_order) VALUES (1, 0)"
        )
        await db.commit()


async def get_last_order(db_path: str) -> int:
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT last_order FROM counter WHERE id=1")
        row = await cursor.fetchone()
        return int(row[0]) if row else 0


async def increment_and_get_order(db_path: str) -> str:
    async with aiosqlite.connect(db_path) as db:
        await db.execute("BEGIN IMMEDIATE")
        cursor = await db.execute("SELECT last_order FROM counter WHERE id=1")
        row = await cursor.fetchone()
        current = int(row[0]) if row else 0
        new_value = current + 1
        await db.execute("UPDATE counter SET last_order=? WHERE id=1", (new_value,))
        await db.commit()
        return f"{new_value:05d}"


async def save_review(db_path: str, review: ReviewLogRecord, timezone: ZoneInfo) -> None:
    created_at = datetime.now(timezone).isoformat(timespec="seconds")
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO reviews_log (
                created_at,
                admin_user_id,
                username,
                pay_date,
                order_no,
                rating,
                review_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                review.admin_user_id,
                review.username,
                review.pay_date,
                review.order_no,
                review.rating,
                review.review_text,
            ),
        )
        await db.commit()
