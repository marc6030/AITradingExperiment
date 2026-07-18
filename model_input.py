from decimal import Decimal

from database import create_tables, get_latest_candles


CANDLE_COUNT = 50


def decimal_from_row(row, column_name: str) -> Decimal:
    """Konverterer en databaseværdi til Decimal."""
    return Decimal(row[column_name])


def calculate_percentage_change(
    current_value: Decimal,
    previous_value: Decimal,
) -> float:
    """
    Beregner procentvis ændring som decimaltal.

    Eksempel:
    100 til 101 bliver 0.01, altså 1 %.
    """
    if previous_value == 0:
        return 0.0

    change = (current_value / previous_value) - Decimal("1")

    return float(change)


def create_features(candles) -> list[list[float]]:
    """
    Konverterer candles til normaliserede features.

    Features per candle:
    1. Open i forhold til forrige close
    2. High i forhold til open
    3. Low i forhold til open
    4. Close i forhold til open
    5. Volume i forhold til forrige volume
    """
    if len(candles) < 2:
        raise ValueError(
            "Der skal være mindst to candles for at beregne features."
        )

    features: list[list[float]] = []

    for index in range(1, len(candles)):
        previous_candle = candles[index - 1]
        current_candle = candles[index]

        previous_close = decimal_from_row(
            previous_candle,
            "close_price",
        )
        previous_volume = decimal_from_row(
            previous_candle,
            "volume",
        )

        current_open = decimal_from_row(
            current_candle,
            "open_price",
        )
        current_high = decimal_from_row(
            current_candle,
            "high_price",
        )
        current_low = decimal_from_row(
            current_candle,
            "low_price",
        )
        current_close = decimal_from_row(
            current_candle,
            "close_price",
        )
        current_volume = decimal_from_row(
            current_candle,
            "volume",
        )

        candle_features = [
            calculate_percentage_change(
                current_open,
                previous_close,
            ),
            calculate_percentage_change(
                current_high,
                current_open,
            ),
            calculate_percentage_change(
                current_low,
                current_open,
            ),
            calculate_percentage_change(
                current_close,
                current_open,
            ),
            calculate_percentage_change(
                current_volume,
                previous_volume,
            ),
        ]

        features.append(candle_features)

    return features


def print_features(
    candles,
    features: list[list[float]],
) -> None:
    print("\nModel-input")
    print("-----------")
    print(f"Candles hentet: {len(candles)}")
    print(f"Feature-rækker: {len(features)}")
    print(f"Features per række: {len(features[0])}")

    print("\nSeneste 5 feature-rækker")
    print("------------------------")

    latest_features = features[-5:]
    latest_candles = candles[-5:]

    for candle, feature_row in zip(
        latest_candles,
        latest_features,
    ):
        print(f"\nTid: {candle['open_time']}")
        print(f"Open change:   {feature_row[0]:.8f}")
        print(f"High change:   {feature_row[1]:.8f}")
        print(f"Low change:    {feature_row[2]:.8f}")
        print(f"Close change:  {feature_row[3]:.8f}")
        print(f"Volume change: {feature_row[4]:.8f}")


def main() -> None:
    create_tables()

    candles = get_latest_candles(CANDLE_COUNT)

    if len(candles) < CANDLE_COUNT:
        print(
            f"Advarsel: Databasen indeholder kun {len(candles)} "
            f"candles. Der forventes {CANDLE_COUNT}."
        )

    if len(candles) < 2:
        print("Der er ikke nok candles til at lave model-input.")
        return

    features = create_features(candles)

    print_features(candles, features)


if __name__ == "__main__":
    main()
