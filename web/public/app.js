const REFRESH_INTERVAL_MS = 5000;

const elements = {
    errorMessage: document.querySelector(
        "#error-message"
    ),

    currentPrice: document.querySelector(
        "#current-price"
    ),

    latestCandleTime: document.querySelector(
        "#latest-candle-time"
    ),

    accountBalance: document.querySelector(
        "#account-balance"
    ),

    totalProfit: document.querySelector(
        "#total-profit"
    ),

    totalReturn: document.querySelector(
        "#total-return"
    ),

    winRate: document.querySelector(
        "#win-rate"
    ),

    totalTrades: document.querySelector(
        "#total-trades"
    ),

    profitFactor: document.querySelector(
        "#profit-factor"
    ),

    tradeStatus: document.querySelector(
        "#trade-status"
    ),

    tradeDirection: document.querySelector(
        "#trade-direction"
    ),

    entryPrice: document.querySelector(
        "#entry-price"
    ),

    positionSize: document.querySelector(
        "#position-size"
    ),

    candlesRemaining: document.querySelector(
        "#candles-remaining"
    ),

    holdingCandles: document.querySelector(
        "#holding-candles"
    ),

    modelVersion: document.querySelector(
        "#model-version"
    ),

    lastUpdated: document.querySelector(
        "#last-updated"
    ),

    historyStatus: document.querySelector(
        "#history-status"
    ),

    tradeHistoryBody: document.querySelector(
        "#trade-history-body"
    ),

};

function formatCurrency(value) {
    if (value === null || value === undefined) {
        return "—";
    }

    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(value);
}

function formatPrice(value) {
    if (value === null || value === undefined) {
        return "—";
    }

    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(value);
}

function formatPercent(value) {
    if (value === null || value === undefined) {
        return "—";
    }

    const sign = value > 0 ? "+" : "";

    return `${sign}${value.toFixed(4)}%`;
}

function formatDate(value) {
    if (!value) {
        return "—";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString();
}

function setValueClass(element, value) {
    element.classList.remove(
        "positive",
        "negative",
        "neutral"
    );

    if (value > 0) {
        element.classList.add("positive");
    } else if (value < 0) {
        element.classList.add("negative");
    } else {
        element.classList.add("neutral");
    }
}

function showError(message) {
    elements.errorMessage.textContent = message;
    elements.errorMessage.classList.remove("hidden");
}

function hideError() {
    elements.errorMessage.classList.add("hidden");
}

function renderMarket(market) {
    if (!market) {
        elements.currentPrice.textContent = "No data";
        elements.latestCandleTime.textContent = "—";
        return;
    }

    elements.currentPrice.textContent =
        formatPrice(market.close);

    elements.latestCandleTime.textContent =
        formatDate(market.closeTime);
}

function renderAccount(account) {
    elements.accountBalance.textContent =
        formatCurrency(account.currentBalance);

    elements.totalProfit.textContent =
        formatCurrency(account.totalProfit);

    elements.totalReturn.textContent =
        formatPercent(account.totalReturnPercent);

    setValueClass(
        elements.totalProfit,
        account.totalProfit
    );

    setValueClass(
        elements.totalReturn,
        account.totalReturnPercent
    );
}

function renderStatistics(statistics) {
    elements.winRate.textContent =
        `${statistics.winRatePercent.toFixed(2)}%`;

    elements.totalTrades.textContent =
        statistics.totalTrades.toString();

    elements.profitFactor.textContent =
        statistics.profitFactor === null
            ? "—"
            : statistics.profitFactor.toFixed(2);
}

function clearTrade() {
    elements.tradeStatus.textContent =
        "No active position";

    elements.tradeDirection.textContent = "—";
    elements.tradeDirection.className =
        "trade-direction";

    elements.entryPrice.textContent = "—";
    elements.positionSize.textContent = "—";
    elements.candlesRemaining.textContent = "—";
    elements.holdingCandles.textContent = "—";
    elements.modelVersion.textContent = "—";
}

function renderTrade(trade) {
    if (!trade) {
        clearTrade();
        return;
    }

    elements.tradeStatus.textContent =
        `Trade #${trade.id} · ${trade.status}`;

    elements.tradeDirection.textContent =
        trade.direction;

    elements.tradeDirection.className =
        `trade-direction ${trade.direction.toLowerCase()}`;

    elements.entryPrice.textContent =
        formatPrice(trade.entryPrice);

    elements.positionSize.textContent =
        formatCurrency(trade.positionSize);

    elements.candlesRemaining.textContent =
        trade.candlesRemaining.toString();

    elements.holdingCandles.textContent =
        `${trade.holdingCandles} minutes`;

    elements.modelVersion.textContent =
        trade.modelVersion;
}


function createTradeRow(trade) {
    const row = document.createElement("tr");

    const returnClass =
        trade.netReturnPercent > 0
            ? "positive"
            : trade.netReturnPercent < 0
                ? "negative"
                : "neutral";

    const pnlClass =
        trade.pnlAmount > 0
            ? "positive"
            : trade.pnlAmount < 0
                ? "negative"
                : "neutral";

    row.innerHTML = `
        <td>#${trade.id}</td>

        <td>
            <span class="direction-badge ${trade.direction.toLowerCase()}">
                ${trade.direction}
            </span>
        </td>

        <td>${formatPrice(trade.entryPrice)}</td>

        <td>${formatPrice(trade.exitPrice)}</td>

        <td>${trade.holdingCandles} min</td>

        <td class="${returnClass}">
            ${formatPercent(trade.netReturnPercent)}
        </td>

        <td class="${pnlClass}">
            ${formatSignedCurrency(trade.pnlAmount)}
        </td>
    `;

    return row;
}

function formatSignedCurrency(value) {
    if (value === null || value === undefined) {
        return "—";
    }

    const sign = value > 0 ? "+" : "";

    return `${sign}${formatCurrency(value)}`;
}

function renderTradeHistory(trades) {
    elements.tradeHistoryBody.innerHTML = "";

    const closedTrades = trades.filter(
        (trade) => trade.status === "CLOSED"
    );

    if (closedTrades.length === 0) {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td colspan="7" class="empty-table">
                No closed trades yet.
            </td>
        `;

        elements.tradeHistoryBody.appendChild(row);
        elements.historyStatus.textContent =
            "0 closed trades";

        return;
    }

    for (const trade of closedTrades) {
        const row = createTradeRow(trade);
        elements.tradeHistoryBody.appendChild(row);
    }

    elements.historyStatus.textContent =
        `${closedTrades.length} shown`;
}

async function loadTradeHistory() {
    try {
        const response = await fetch(
            "/api/trades?limit=20",
            {
                cache: "no-store",
            }
        );

        if (!response.ok) {
            throw new Error(
                `Trade API returned ${response.status}`
            );
        }

        const data = await response.json();

        renderTradeHistory(data.trades);
    } catch (error) {
        console.error(error);

        elements.historyStatus.textContent =
            "Could not load trades";

        elements.tradeHistoryBody.innerHTML = `
            <tr>
                <td colspan="7" class="empty-table">
                    Could not load trade history.
                </td>
            </tr>
        `;
    }
}


async function loadStatus() {
    try {
        const response = await fetch(
            "/api/status",
            {
                cache: "no-store",
            }
        );

        if (!response.ok) {
            throw new Error(
                `API returned ${response.status}`
            );
        }

        const status = await response.json();

        renderMarket(status.market);
        renderAccount(status.account);
        renderStatistics(status.statistics);
        renderTrade(status.openTrade);

        elements.lastUpdated.textContent =
            `Updated ${new Date().toLocaleTimeString()}`;

        hideError();
    } catch (error) {
        console.error(error);

        showError(
            "Could not load live trading data."
        );

        elements.lastUpdated.textContent =
            "Connection error";
    }
}

async function refreshPage() {
    await Promise.all([
        loadStatus(),
        loadTradeHistory(),
    ]);
}

refreshPage();

setInterval(
    refreshPage,
    REFRESH_INTERVAL_MS
);
