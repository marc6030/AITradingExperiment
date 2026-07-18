from database import (
    create_tables,
    create_trade,
    get_latest_candles,
    get_open_trade,
    get_trade_count,
)
from model_input import create_features
from random_model import RandomTradingModel


CANDLES_NEEDED = 51


def print_trade(trade) -> None:
    print("\nÅben handel")
    print("-----------")
    print(f"Trade ID:          {trade['id']}")
    print(f"Marked:            {trade['symbol']}")
    print(f"Retning:           {trade['direction']}")
    print(f"Entry-tid:         {trade['entry_time']}")
    print(f"Entry-pris:        {trade['entry_price']}")
    print(f"Holdetid:          {trade['holding_candles']} candles")
    print(f"Candles tilbage:   {trade['candles_remaining']}")
    print(f"Confidence:        {trade['confidence']:.2%}")
    print(f"Modelversion:      {trade['model_version']}")
    print(f"Status:            {trade['status']}")


def main() -> None:
    create_tables()

    existing_trade = get_open_trade()

    if existing_trade is not None:
        print("Der findes allerede en åben handel.")
        print_trade(existing_trade)
        return

    candles = get_latest_candles(CANDLES_NEEDED)

    if len(candles) < CANDLES_NEEDED:
        print(
            f"Der er kun {len(candles)} candles i databasen. "
            f"Der kræves mindst {CANDLES_NEEDED}."
        )
        return

    features = create_features(candles)

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

    trade = get_open_trade()

    print("\nNy virtuel handel oprettet")
    print("--------------------------")
    print(f"Trade ID: {trade_id}")

    if trade is not None:
        print_trade(trade)

    print(f"\nSamlet antal handler: {get_trade_count()}")


if __name__ == "__main__":
    main()
