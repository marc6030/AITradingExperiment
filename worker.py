import time
from datetime import datetime, timezone

from database import create_tables, get_candle_count, save_candle
from market_data import fetch_latest_closed_candle


CHECK_INTERVAL_SECONDS = 5


def wait_until_next_check() -> None:
    """
    Venter et kort interval før næste kontrol.

    Vi tjekker hvert 5. sekund, men databasen beskytter
    automatisk mod dubletter.
    """
    time.sleep(CHECK_INTERVAL_SECONDS)


def print_status(message: str) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"[{now}] {message}", flush=True)


def run_worker() -> None:
    create_tables()

    print_status("Trading-worker startet.")
    print_status(f"Candles i databasen: {get_candle_count()}")

    while True:
        try:
            candle = fetch_latest_closed_candle()
            was_saved = save_candle(candle)

            if was_saved:
                print_status(
                    "Ny candle gemt: "
                    f"{candle['open_time'].isoformat()} | "
                    f"Close: {candle['close']} | "
                    f"Total: {get_candle_count()}"
                )

        except RuntimeError as error:
            print_status(f"Datafejl: {error}")

        except Exception as error:
            print_status(f"Uventet fejl: {error}")

        wait_until_next_check()


if __name__ == "__main__":
    run_worker()
