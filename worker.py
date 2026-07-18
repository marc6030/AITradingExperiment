import time
from datetime import datetime, timezone
from typing import Any

from database import (
    close_trade,
    create_tables,
    create_trade,
    decrease_trade_countdown,
    get_account,
    get_candle_count,
    get_latest_candles,
    get_open_trade,
    save_candle,
)
from market_data import fetch_latest_closed_candle
from model_input import create_features
from random_model import RandomTradingModel


CHECK_INTERVAL_SECONDS = 5
CANDLES_NEEDED = 51


def wait_until_next_check() -> None:
    time.sleep(CHECK_INTERVAL_SECONDS)


def print_status(message: str) -> None:
    now = datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    )

    print(f"[{now}] {message}", flush=True)


def print_closed_trade(trade) -> None:
    net_return = float(
        trade["net_return_percent"]
    )
    pnl_amount = float(trade["pnl_amount"])
    balance_after = float(trade["balance_after"])
    position_size = float(trade["position_size"])

    if pnl_amount > 0:
        result_text = "GEVINST"
    elif pnl_amount < 0:
        result_text = "TAB"
    else:
        result_text = "BREAK-EVEN"

    print_status(
        f"Trade #{trade['id']} lukket | "
        f"{trade['direction']} | "
        f"Position: ${position_size:.2f} | "
        f"Netto: {net_return:.4f}% | "
        f"P/L: ${pnl_amount:+.2f} | "
        f"Saldo: ${balance_after:.2f} | "
        f"{result_text}"
    )


def open_new_trade() -> None:
    """
    Bruger de seneste 51 candles til at lave 50 feature-rækker
    og åbner derefter en ny virtuel handel.
    """
    if get_open_trade() is not None:
        return

    candles = get_latest_candles(CANDLES_NEEDED)

    if len(candles) < CANDLES_NEEDED:
        print_status(
            f"Kan ikke åbne trade. Kun {len(candles)} candles "
            f"fundet; der kræves {CANDLES_NEEDED}."
        )
        return

    features = create_features(candles)

    if len(features) != 50:
        print_status(
            f"Forkert antal feature-rækker: {len(features)}."
        )
        return

    model = RandomTradingModel()
    decision = model.predict(features)

    latest_candle = candles[-1]

    trade_id = create_trade(
        symbol=latest_candle["symbol"],
        direction=decision.direction,
        entry_time=latest_candle["close_time"],
        entry_price=latest_candle["close_price"],
        holding_candles=decision.holding_candles,
        confidence=decision.confidence,
        model_version=decision.model_version,
    )

    print_status(
        f"Ny trade #{trade_id} åbnet | "
        f"{decision.direction} | "
        f"Entry: {latest_candle['close_price']} | "
        f"Holdetid: {decision.holding_candles} candles | "
        f"Confidence: {decision.confidence:.2%} | "
        f"Model: {decision.model_version}"
    )


def process_open_trade(candle: dict[str, Any]) -> None:
    """
    Tæller den aktuelle handel ned og lukker den ved nul.
    """
    trade = get_open_trade()

    if trade is None:
        return

    candles_remaining = decrease_trade_countdown(
        trade["id"]
    )

    print_status(
        f"Trade #{trade['id']} | "
        f"{trade['direction']} | "
        f"Candles tilbage: {candles_remaining}"
    )

    if candles_remaining == 0:
        closed_trade = close_trade(
            trade_id=trade["id"],
            exit_time=candle["close_time"].isoformat(),
            exit_price=str(candle["close"]),
        )

        print_closed_trade(closed_trade)


def process_new_candle(candle: dict[str, Any]) -> None:
    """
    Behandler én ny afsluttet candle.

    Først håndteres den eksisterende handel.
    Derefter åbnes en ny handel, hvis ingen er åben.
    """
    process_open_trade(candle)
    open_new_trade()


def run_worker() -> None:
    create_tables()

    account = get_account()

    print_status(
        f"Virtuel saldo: "
        f"${float(account['current_balance']):.2f}"
    )

    print_status("Trading-worker startet.")
    print_status(
        f"Candles i databasen: {get_candle_count()}"
    )

    open_trade = get_open_trade()

    if open_trade is not None:
        print_status(
            f"Åben trade fundet: "
            f"#{open_trade['id']} "
            f"{open_trade['direction']} | "
            f"{open_trade['candles_remaining']} candles tilbage"
        )
    else:
        print_status(
            "Ingen åben trade. En ny åbnes ved næste nye candle."
        )

    while True:
        try:
            candle = fetch_latest_closed_candle()
            was_saved = save_candle(candle)

            if was_saved:
                print_status(
                    f"Ny candle gemt | "
                    f"{candle['open_time'].isoformat()} | "
                    f"Close: {candle['close']} | "
                    f"Total: {get_candle_count()}"
                )

                process_new_candle(candle)

        except RuntimeError as error:
            print_status(f"Datafejl: {error}")

        except KeyboardInterrupt:
            print_status("Trading-worker stoppet.")
            break

        except Exception as error:
            print_status(
                f"Uventet fejl: "
                f"{type(error).__name__}: {error}"
            )

        wait_until_next_check()


if __name__ == "__main__":
    run_worker()
