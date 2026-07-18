from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import requests

from database import (
    create_tables,
    get_candle_count,
    get_latest_candle,
    save_candle,
)


BASE_URL = "https://api.binance.com"
SYMBOL = "BTCUSDT"
INTERVAL = "1m"
TIMEOUT_SECONDS = 10


def milliseconds_to_utc(timestamp_ms: int) -> datetime:
    """Konverterer Unix-tid i millisekunder til UTC."""
    return datetime.fromtimestamp(
        timestamp_ms / 1000,
        tz=timezone.utc,
    )


def fetch_latest_closed_candle() -> dict[str, Any]:
    """
    Henter de to seneste candles og returnerer den næstsidste.

    Den sidste candle er normalt stadig åben.
    Den næstsidste er derfor den seneste afsluttede candle.
    """
    url = f"{BASE_URL}/api/v3/klines"

    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "limit": 2,
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise RuntimeError(
            f"Kunne ikke hente markedsdata: {error}"
        ) from error

    candles = response.json()

    if not isinstance(candles, list) or len(candles) < 2:
        raise RuntimeError(
            "Binance returnerede ikke mindst to candles."
        )

    closed_candle = candles[-2]

    return {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "open_time": milliseconds_to_utc(closed_candle[0]),
        "open": Decimal(closed_candle[1]),
        "high": Decimal(closed_candle[2]),
        "low": Decimal(closed_candle[3]),
        "close": Decimal(closed_candle[4]),
        "volume": Decimal(closed_candle[5]),
        "close_time": milliseconds_to_utc(closed_candle[6]),
        "number_of_trades": int(closed_candle[8]),
    }


def print_candle(candle: dict[str, Any]) -> None:
    print("\nSeneste afsluttede candle")
    print("--------------------------")
    print(f"Marked:       {candle['symbol']}")
    print(f"Interval:     {candle['interval']}")
    print(f"Åbnede:       {candle['open_time'].isoformat()}")
    print(f"Lukkede:      {candle['close_time'].isoformat()}")
    print(f"Open:         {candle['open']}")
    print(f"High:         {candle['high']}")
    print(f"Low:          {candle['low']}")
    print(f"Close:        {candle['close']}")
    print(f"Volume:       {candle['volume']}")
    print(f"Antal trades: {candle['number_of_trades']}")


def print_latest_saved_candle() -> None:
    candle = get_latest_candle()

    if candle is None:
        print("Databasen indeholder ingen candles.")
        return

    print("\nSeneste candle i databasen")
    print("---------------------------")
    print(f"ID:        {candle['id']}")
    print(f"Marked:    {candle['symbol']}")
    print(f"Åbning:    {candle['open_time']}")
    print(f"Lukkepris: {candle['close_price']}")


def main() -> None:
    try:
        create_tables()

        candle = fetch_latest_closed_candle()
        print_candle(candle)

        was_saved = save_candle(candle)

        if was_saved:
            print("\nCandlen blev gemt i databasen.")
        else:
            print("\nCandlen fandtes allerede i databasen.")

        print(f"Antal gemte candles: {get_candle_count()}")
        print_latest_saved_candle()

    except RuntimeError as error:
        print(f"Fejl: {error}")
    except sqlite3.Error as error:
        print(f"Databasefejl: {error}")


if __name__ == "__main__":
    import sqlite3

    main()
