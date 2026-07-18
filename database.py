import sqlite3
from pathlib import Path
from typing import Any
from decimal import Decimal


DATABASE_PATH = Path(__file__).parent / "trading.db"

INITIAL_BALANCE = Decimal("10000.00")
POSITION_SIZE_PERCENT = Decimal("10.00")

def get_connection() -> sqlite3.Connection:
    """Åbner en forbindelse til SQLite-databasen."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables() -> None:
    """Opretter og opdaterer alle nødvendige tabeller."""
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

    create_trade_table()
    migrate_trade_table()
    create_account_table()


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


def get_latest_candles(limit: int = 50) -> list[sqlite3.Row]:
    """
    Henter de seneste candles i kronologisk rækkefølge.

    Den ældste candle kommer først.
    Den nyeste candle kommer sidst.
    """
    if limit <= 0:
        raise ValueError("Limit skal være større end 0.")

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM candles
            ORDER BY open_time DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return list(reversed(rows))

def create_trade(
    symbol: str,
    direction: str,
    entry_time: str,
    entry_price: str,
    holding_candles: int,
    confidence: float,
    model_version: str,
) -> int:
    """
    Opretter en virtuel handel med 10 % af kontosaldoen.
    """
    if direction not in {"LONG", "SHORT"}:
        raise ValueError(
            "Direction skal være LONG eller SHORT."
        )

    if holding_candles <= 0:
        raise ValueError(
            "Holding candles skal være større end 0."
        )

    if get_open_trade() is not None:
        raise RuntimeError(
            "Der findes allerede en åben handel."
        )

    account = get_account()
    balance = Decimal(account["current_balance"])

    position_size = calculate_position_size(balance)

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO trades (
                symbol,
                direction,
                entry_time,
                entry_price,
                holding_candles,
                candles_remaining,
                confidence,
                model_version,
                status,
                position_size
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
            """,
            (
                symbol,
                direction,
                entry_time,
                entry_price,
                holding_candles,
                holding_candles,
                confidence,
                model_version,
                str(position_size),
            ),
        )

        return int(cursor.lastrowid)


def get_open_trade() -> sqlite3.Row | None:
    """Henter den åbne handel, hvis der findes en."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM trades
            WHERE status = 'OPEN'
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    return row


def create_trade(
    symbol: str,
    direction: str,
    entry_time: str,
    entry_price: str,
    holding_candles: int,
    confidence: float,
    model_version: str,
) -> int:
    """
    Opretter en ny virtuel handel.

    Returnerer ID'et på den nye handel.
    """
    if direction not in {"LONG", "SHORT"}:
        raise ValueError("Direction skal være LONG eller SHORT.")

    if holding_candles <= 0:
        raise ValueError("Holding candles skal være større end 0.")

    if get_open_trade() is not None:
        raise RuntimeError("Der findes allerede en åben handel.")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO trades (
                symbol,
                direction,
                entry_time,
                entry_price,
                holding_candles,
                candles_remaining,
                confidence,
                model_version,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')
            """,
            (
                symbol,
                direction,
                entry_time,
                entry_price,
                holding_candles,
                holding_candles,
                confidence,
                model_version,
            ),
        )

        return int(cursor.lastrowid)


def get_trade_count() -> int:
    """Returnerer det samlede antal handler."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS trade_count
            FROM trades
            """
        ).fetchone()

    return int(row["trade_count"])

def decrease_trade_countdown(trade_id: int) -> int:
    """
    Reducerer candles_remaining med 1.

    Returnerer det nye antal candles tilbage.
    """
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE trades
            SET candles_remaining =
                CASE
                    WHEN candles_remaining > 0
                    THEN candles_remaining - 1
                    ELSE 0
                END
            WHERE id = ?
              AND status = 'OPEN'
            """,
            (trade_id,),
        )

        row = connection.execute(
            """
            SELECT candles_remaining
            FROM trades
            WHERE id = ?
            """,
            (trade_id,),
        ).fetchone()

    if row is None:
        raise RuntimeError(
            f"Kunne ikke finde trade med ID {trade_id}."
        )

    return int(row["candles_remaining"])

def calculate_trade_return(
    direction: str,
    entry_price: Decimal,
    exit_price: Decimal,
    fee_percent: Decimal = Decimal("0.10"),
) -> tuple[Decimal, Decimal]:
    """
    Beregner brutto- og nettoafkast i procent.

    Eksempel:
    0.25 betyder 0,25 %, ikke 25 %.
    """
    if entry_price <= 0:
        raise ValueError("Entry-prisen skal være større end 0.")

    if exit_price <= 0:
        raise ValueError("Exit-prisen skal være større end 0.")

    if direction == "LONG":
        gross_return_percent = (
            (exit_price - entry_price) / entry_price
        ) * Decimal("100")

    elif direction == "SHORT":
        gross_return_percent = (
            (entry_price - exit_price) / entry_price
        ) * Decimal("100")

    else:
        raise ValueError("Direction skal være LONG eller SHORT.")

    net_return_percent = gross_return_percent - fee_percent

    return gross_return_percent, net_return_percent


def close_trade(
    trade_id: int,
    exit_time: str,
    exit_price: str,
    fee_percent: Decimal = Decimal("0.10"),
) -> sqlite3.Row:
    """
    Lukker en handel og opdaterer kontosaldoen.

    Afkastet påvirker kun positionens størrelse,
    ikke hele kontoen.
    """
    with get_connection() as connection:
        trade = connection.execute(
            """
            SELECT *
            FROM trades
            WHERE id = ?
              AND status = 'OPEN'
            """,
            (trade_id,),
        ).fetchone()

        if trade is None:
            raise RuntimeError(
                f"Der findes ingen åben trade med ID {trade_id}."
            )

        account = connection.execute(
            """
            SELECT *
            FROM account
            WHERE id = 1
            """
        ).fetchone()

        if account is None:
            raise RuntimeError(
                "Den virtuelle konto findes ikke."
            )

        entry_price_decimal = Decimal(
            trade["entry_price"]
        )
        exit_price_decimal = Decimal(exit_price)

        gross_return, net_return = calculate_trade_return(
            direction=trade["direction"],
            entry_price=entry_price_decimal,
            exit_price=exit_price_decimal,
            fee_percent=fee_percent,
        )

        current_balance = Decimal(
            account["current_balance"]
        )

        if trade["position_size"] is None:
            position_size = calculate_position_size(
                current_balance
            )
        else:
            position_size = Decimal(
                trade["position_size"]
            )

        pnl_amount = (
            position_size
            * net_return
            / Decimal("100")
        ).quantize(Decimal("0.01"))

        new_balance = (
            current_balance + pnl_amount
        ).quantize(Decimal("0.01"))

        connection.execute(
            """
            UPDATE trades
            SET status = 'CLOSED',
                candles_remaining = 0,
                exit_time = ?,
                exit_price = ?,
                gross_return_percent = ?,
                net_return_percent = ?,
                position_size = ?,
                pnl_amount = ?,
                balance_after = ?
            WHERE id = ?
              AND status = 'OPEN'
            """,
            (
                exit_time,
                str(exit_price_decimal),
                float(gross_return),
                float(net_return),
                str(position_size),
                str(pnl_amount),
                str(new_balance),
                trade_id,
            ),
        )

        connection.execute(
            """
            UPDATE account
            SET current_balance = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            (str(new_balance),),
        )

        closed_trade = connection.execute(
            """
            SELECT *
            FROM trades
            WHERE id = ?
            """,
            (trade_id,),
        ).fetchone()

    if closed_trade is None:
        raise RuntimeError(
            "Handlen kunne ikke læses efter lukning."
        )

    return closed_trade


def get_latest_closed_trade() -> sqlite3.Row | None:
    """Henter den senest lukkede handel."""
    with get_connection() as connection:
        trade = connection.execute(
            """
            SELECT *
            FROM trades
            WHERE status = 'CLOSED'
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    return trade

def get_closed_trades() -> list[sqlite3.Row]:
    """Henter alle lukkede handler i kronologisk rækkefølge."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM trades
            WHERE status = 'CLOSED'
            ORDER BY id ASC
            """
        ).fetchall()

    return list(rows)


def column_exists(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
) -> bool:
    """Kontrollerer om en kolonne allerede findes."""
    columns = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return any(
        column["name"] == column_name
        for column in columns
    )


def migrate_trade_table() -> None:
    """
    Tilføjer nye kolonner til en eksisterende trades-tabel.

    Det betyder, at du ikke behøver slette trading.db.
    """
    with get_connection() as connection:
        if not column_exists(
            connection,
            "trades",
            "position_size",
        ):
            connection.execute(
                """
                ALTER TABLE trades
                ADD COLUMN position_size TEXT
                """
            )

        if not column_exists(
            connection,
            "trades",
            "pnl_amount",
        ):
            connection.execute(
                """
                ALTER TABLE trades
                ADD COLUMN pnl_amount TEXT
                """
            )

        if not column_exists(
            connection,
            "trades",
            "balance_after",
        ):
            connection.execute(
                """
                ALTER TABLE trades
                ADD COLUMN balance_after TEXT
                """
            )


def create_account_table() -> None:
    """Opretter den virtuelle konto."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS account (
                id INTEGER PRIMARY KEY CHECK(id = 1),
                initial_balance TEXT NOT NULL,
                current_balance TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.execute(
            """
            INSERT OR IGNORE INTO account (
                id,
                initial_balance,
                current_balance
            )
            VALUES (1, ?, ?)
            """,
            (
                str(INITIAL_BALANCE),
                str(INITIAL_BALANCE),
            ),
        )


def get_account() -> sqlite3.Row:
    """Henter den virtuelle konto."""
    with get_connection() as connection:
        account = connection.execute(
            """
            SELECT *
            FROM account
            WHERE id = 1
            """
        ).fetchone()

    if account is None:
        raise RuntimeError(
            "Den virtuelle konto findes ikke."
        )

    return account


def calculate_position_size(
    balance: Decimal,
    position_size_percent: Decimal = POSITION_SIZE_PERCENT,
) -> Decimal:
    """Beregner hvor mange dollars der bruges på en handel."""
    if balance <= 0:
        raise ValueError(
            "Saldoen skal være større end 0."
        )

    return (
        balance * position_size_percent / Decimal("100")
    ).quantize(Decimal("0.01"))

def create_trade_table() -> None:
    """Opretter trades-tabellen, hvis den ikke allerede findes."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL
                    CHECK(direction IN ('LONG', 'SHORT')),
                entry_time TEXT NOT NULL,
                entry_price TEXT NOT NULL,
                holding_candles INTEGER NOT NULL,
                candles_remaining INTEGER NOT NULL,
                confidence REAL NOT NULL,
                model_version TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'OPEN'
                    CHECK(status IN ('OPEN', 'CLOSED')),
                exit_time TEXT,
                exit_price TEXT,
                gross_return_percent REAL,
                net_return_percent REAL,
                position_size TEXT,
                pnl_amount TEXT,
                balance_after TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
