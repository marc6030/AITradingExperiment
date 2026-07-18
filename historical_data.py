from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import requests

from database import (
    create_tables,
    get_candle_count,
    get_latest_candle,
    save_candles,
)


BASE_URL = "https://data-api.binance.vision"
SYMBOL = "BTCUSDT"
INTERVAL = "1m"

CLOSED_CANDLES_TO_FETCH = 500
TIMEOUT_SECONDS = 15


def milliseconds_to_utc(timestamp_ms: int) -> datetime:
    """Konverterer Unix-tid i millisekunder til UTC."""
    return datetime.fromtimestamp(
        timestamp_ms / 1000,
        tz=timezone.utc,
    )


def parse_candle(raw_candle: list[Any]) -> dict[str, Any]:
    """Konverterer Binances candle-format til vores eget format."""
    return {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "open_time": milliseconds_to_utc(raw_candle[0]),
        "open": Decimal(raw_candle[1]),
        "high": Decimal(raw_candle[2]),
        "low": Decimal(raw_candle[3]),
        "close": Decimal(raw_candle[4]),
        "volume": Decimal(raw_candle[5]),
        "close_time": milliseconds_to_utc(raw_candle[6]),
        "number_of_trades": int(raw_candle[8]),
    }


def fetch_historical_closed_candles() -> list[dict[str, Any]]:
    """
    Henter de seneste 500 afsluttede candles.

    Vi henter 501 og fjerner den sidste, fordi den normalt
    er den aktive candle, som endnu ikke er afsluttet.
    """
    url = f"{BASE_URL}/api/v3/klines"

    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "limit": CLOSED_CANDLES_TO_FETCH + 1,
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
            f"Kunne ikke hente historiske candles: {error}"
        ) from error

    raw_candles = response.json()

    if not isinstance(raw_candles, list):
        raise RuntimeError(
            "Binance returnerede data i et ukendt format."
        )

    if len(raw_candles) < 2:
        raise RuntimeError(
            "Binance returnerede ikke nok candles."
        )

    closed_raw_candles = raw_candles[:-1]

    return [
        parse_candle(raw_candle)
        for raw_candle in closed_raw_candles
    ]


def print_summary(
    candles: list[dict[str, Any]],
    inserted_count: int,
) -> None:
    first_candle = candles[0]
    last_candle = candles[-1]

    print("\nHistoriske candles")
    print("-------------------")
    print(f"Modtaget:          {len(candles)}")
    print(f"Nye gemte candles: {inserted_count}")
    print(f"Første candle:     {first_candle['open_time'].isoformat()}")
    print(f"Seneste candle:    {last_candle['open_time'].isoformat()}")
    print(f"Første lukkepris:  {first_candle['close']}")
    print(f"Seneste lukkepris: {last_candle['close']}")
    print(f"Total i databasen: {get_candle_count()}")


def main() -> None:
    try:
        create_tables()

        candles = fetch_historical_closed_candles()
        inserted_count = save_candles(candles)

        print_summary(candles, inserted_count)

        latest = get_latest_candle()

        if latest is not None:
            print("\nSeneste candle i databasen")
            print("---------------------------")
            print(f"ID:        {latest['id']}")
            print(f"Åbning:    {latest['open_time']}")
            print(f"Lukkepris: {latest['close_price']}")

    except RuntimeError as error:
        print(f"Fejl: {error}")


if __name__ == "__main__":
    main()
