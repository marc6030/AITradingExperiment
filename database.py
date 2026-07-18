import sqlite3
from pathlib import Path
from typing import Any


DATABASE_PATH = Path(__file__).parent / "trading.db"


def get_connection() -> sqlite3.Connection:
    """Åbner en forbindelse til SQLite-databasen."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables() -> None:
    """Opretter candles-tabellen, hvis den ikke allerede findes."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS candles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                interval TEXT NOT NULL,
                open_time TEXT NOT NULL,
                close_time TEXT NOT NULL,
                open_price TEXT NOT NULL,
                high_price TEXT NOT NULL,
                low_price TEXT NOT NULL,
                close_price TEXT NOT NULL,
                volume TEXT NOT NULL,
                number_of_trades INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(symbol, interval, open_time)
            )
            """
        )


def save_candle(candle: dict[str, Any]) -> bool:
    """
    Gemmer en candle.

    Returnerer True, hvis candlen blev gemt.
    Returnerer False, hvis candlen allerede fandtes.
    """
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO candles (
                symbol,
                interval,
                open_time,
                close_time,
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
                number_of_trades
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                candle["symbol"],
                candle["interval"],
                candle["open_time"].isoformat(),
                candle["close_time"].isoformat(),
                str(candle["open"]),
                str(candle["high"]),
                str(candle["low"]),
                str(candle["close"]),
                str(candle["volume"]),
                candle["number_of_trades"],
            ),
        )

        return cursor.rowcount == 1


def save_candles(candles: list[dict[str, Any]]) -> int:
    """
    Gemmer flere candles i én databaseoperation.

    Returnerer antallet af nye candles, der blev gemt.
    Eksisterende candles ignoreres.
    """
    rows = [
        (
            candle["symbol"],
            candle["interval"],
            candle["open_time"].isoformat(),
            candle["close_time"].isoformat(),
            str(candle["open"]),
            str(candle["high"]),
            str(candle["low"]),
            str(candle["close"]),
            str(candle["volume"]),
            candle["number_of_trades"],
        )
        for candle in candles
    ]

    with get_connection() as connection:
        before_count = connection.total_changes

        connection.executemany(
            """
            INSERT OR IGNORE INTO candles (
                symbol,
                interval,
                open_time,
                close_time,
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
                number_of_trades
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

        return connection.total_changes - before_count

def get_candle_count() -> int:
    """Returnerer antal candles i databasen."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS candle_count FROM candles"
        ).fetchone()

    return int(row["candle_count"])


def get_latest_candle() -> sqlite3.Row | None:
    """Henter den seneste candle fra databasen."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM candles
            ORDER BY open_time DESC
            LIMIT 1
            """
        ).fetchone()

    return row
