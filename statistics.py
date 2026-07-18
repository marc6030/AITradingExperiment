from dataclasses import dataclass

from database import create_tables, get_closed_trades


@dataclass
class TradingStatistics:
    total_trades: int
    winning_trades: int
    losing_trades: int
    break_even_trades: int
    win_rate_percent: float
    total_net_return_percent: float
    average_net_return_percent: float
    best_trade_percent: float
    worst_trade_percent: float
    profit_factor: float | None


def calculate_statistics(trades) -> TradingStatistics:
    """
    Beregner statistik ud fra lukkede handler.

    Samlet afkast beregnes her som summen af handlernes
    procentvise afkast. Senere laver vi rigtig kontoværdi
    med compounding.
    """
    if not trades:
        return TradingStatistics(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            break_even_trades=0,
            win_rate_percent=0.0,
            total_net_return_percent=0.0,
            average_net_return_percent=0.0,
            best_trade_percent=0.0,
            worst_trade_percent=0.0,
            profit_factor=None,
        )

    returns = [
        float(trade["net_return_percent"])
        for trade in trades
    ]

    winning_returns = [
        trade_return
        for trade_return in returns
        if trade_return > 0
    ]

    losing_returns = [
        trade_return
        for trade_return in returns
        if trade_return < 0
    ]

    break_even_returns = [
        trade_return
        for trade_return in returns
        if trade_return == 0
    ]

    total_trades = len(returns)
    winning_trades = len(winning_returns)
    losing_trades = len(losing_returns)
    break_even_trades = len(break_even_returns)

    win_rate_percent = (
        winning_trades / total_trades
    ) * 100

    total_net_return_percent = sum(returns)

    average_net_return_percent = (
        total_net_return_percent / total_trades
    )

    gross_profit = sum(winning_returns)
    gross_loss = abs(sum(losing_returns))

    if gross_loss == 0:
        profit_factor = None
    else:
        profit_factor = gross_profit / gross_loss

    return TradingStatistics(
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        break_even_trades=break_even_trades,
        win_rate_percent=win_rate_percent,
        total_net_return_percent=total_net_return_percent,
        average_net_return_percent=average_net_return_percent,
        best_trade_percent=max(returns),
        worst_trade_percent=min(returns),
        profit_factor=profit_factor,
    )


def format_profit_factor(
    profit_factor: float | None,
) -> str:
    if profit_factor is None:
        return "Ikke beregnelig endnu"

    return f"{profit_factor:.2f}"


def print_statistics(
    statistics: TradingStatistics,
) -> None:
    print("\nTrading-statistik")
    print("-----------------")
    print(f"Antal handler:         {statistics.total_trades}")
    print(f"Gevinster:             {statistics.winning_trades}")
    print(f"Tab:                   {statistics.losing_trades}")
    print(f"Break-even:            {statistics.break_even_trades}")
    print(f"Winrate:               {statistics.win_rate_percent:.2f}%")
    print(
        "Samlet nettoafkast:   "
        f"{statistics.total_net_return_percent:.4f}%"
    )
    print(
        "Gennemsnit per trade: "
        f"{statistics.average_net_return_percent:.4f}%"
    )
    print(
        "Bedste handel:        "
        f"{statistics.best_trade_percent:.4f}%"
    )
    print(
        "Værste handel:        "
        f"{statistics.worst_trade_percent:.4f}%"
    )
    print(
        "Profit factor:        "
        f"{format_profit_factor(statistics.profit_factor)}"
    )


def main() -> None:
    create_tables()

    trades = get_closed_trades()
    statistics = calculate_statistics(trades)

    if not trades:
        print("Der er endnu ingen lukkede handler.")
        return

    print_statistics(statistics)


if __name__ == "__main__":
    main()
