import random
from dataclasses import dataclass


MIN_HOLDING_CANDLES = 5
MAX_HOLDING_CANDLES = 20


@dataclass
class TradingDecision:
    direction: str
    holding_candles: int
    confidence: float
    model_version: str


class RandomTradingModel:
    """
    Simpel testmodel.

    Modellen vælger tilfældigt LONG eller SHORT
    og en holdetid mellem 5 og 20 candles.
    """

    MODEL_VERSION = "random_v1"

    def predict(
        self,
        features: list[list[float]],
    ) -> TradingDecision:
        if not features:
            raise ValueError("Modellen modtog ingen features.")

        direction = random.choice(["LONG", "SHORT"])

        holding_candles = random.randint(
            MIN_HOLDING_CANDLES,
            MAX_HOLDING_CANDLES,
        )

        confidence = random.uniform(0.50, 1.00)

        return TradingDecision(
            direction=direction,
            holding_candles=holding_candles,
            confidence=confidence,
            model_version=self.MODEL_VERSION,
        )
