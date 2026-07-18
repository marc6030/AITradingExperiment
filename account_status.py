from database import (
    create_tables,
    get_account,
    get_open_trade,
)


def main() -> None:
    create_tables()

    account = get_account()

    initial_balance = float(
        account["initial_balance"]
    )
    current_balance = float(
        account["current_balance"]
    )

    total_profit = (
        current_balance - initial_balance
    )

    total_return = (
        total_profit / initial_balance * 100
    )

    print("\nVirtuel konto")
    print("-------------")
    print(f"Startsaldo:     ${initial_balance:.2f}")
    print(f"Nuværende saldo:${current_balance:.2f}")
    print(f"Samlet P/L:     ${total_profit:+.2f}")
    print(f"Samlet afkast:  {total_return:+.4f}%")

    trade = get_open_trade()

    if trade is None:
        print("\nIngen åben handel.")
    else:
        print("\nÅben handel")
        print("-----------")
        print(f"Trade ID:       {trade['id']}")
        print(f"Retning:        {trade['direction']}")
        print(
            f"Positionsværdi: "
            f"${float(trade['position_size'] or 0):.2f}"
        )
        print(
            f"Candles tilbage:"
            f" {trade['candles_remaining']}"
        )


if __name__ == "__main__":
    main()
