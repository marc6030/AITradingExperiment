from database import (
    create_tables,
    get_equity_history,
)


def main() -> None:
    create_tables()

    history = get_equity_history()

    if not history:
        print("Der findes ingen equity-historik.")
        return

    print("\nEquity-historik")
    print("---------------")

    for point in history:
        trade_text = (
            f"Trade #{point['trade_id']}"
            if point["trade_id"] is not None
            else "Start"
        )

        print(
            f"{point['timestamp']} | "
            f"{trade_text:<10} | "
            f"Saldo: ${float(point['balance']):.2f} | "
            f"P/L: {float(point['total_profit']):+.2f} USD | "
            f"Afkast: {float(point['total_return_percent']):+.4f}%"
        )

    latest = history[-1]

    print("\nSeneste punkt")
    print("-------------")
    print(f"Saldo:  ${float(latest['balance']):.2f}")
    print(
        f"P/L:    "
        f"{float(latest['total_profit']):+.2f} USD"
    )
    print(
        f"Afkast: "
        f"{float(latest['total_return_percent']):+.4f}%"
    )


if __name__ == "__main__":
    main()
