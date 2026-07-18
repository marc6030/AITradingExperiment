from database import create_tables, get_latest_candles
from model_input import create_features
from random_model import RandomTradingModel


CANDLES_NEEDED = 51


def main() -> None:
    create_tables()

    candles = get_latest_candles(CANDLES_NEEDED)

    if len(candles) < CANDLES_NEEDED:
        print(
            f"Der er kun {len(candles)} candles i databasen. "
            f"Der skal bruges mindst {CANDLES_NEEDED}."
        )
        return

    features = create_features(candles)

    if len(features) != 50:
        print(
            f"Fejl: Der blev lavet {len(features)} feature-rækker. "
            "Der forventes 50."
        )
        return

    model = RandomTradingModel()
    decision = model.predict(features)

    print("\nModelbeslutning")
    print("----------------")
    print(f"Retning:        {decision.direction}")
    print(f"Holdetid:       {decision.holding_candles} candles")
    print(f"Confidence:     {decision.confidence:.2%}")
    print(f"Modelversion:   {decision.model_version}")
    print(f"Feature-rækker: {len(features)}")


if __name__ == "__main__":
    main()
