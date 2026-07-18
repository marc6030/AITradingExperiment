const express = require("express");
const path = require("path");
const sqlite3 = require("sqlite3");
const { open } = require("sqlite");

const app = express();

const PORT = 3000;

// trading.db ligger én mappe over web-mappen.
const DATABASE_PATH = path.join(__dirname, "..", "trading.db");

let database;

app.use(express.json());

app.use(express.static(
    path.join(__dirname, "public")
));

function parseNumber(value) {
    if (value === null || value === undefined) {
        return null;
    }

    const parsedValue = Number(value);

    return Number.isFinite(parsedValue)
        ? parsedValue
        : null;
}

function formatAccount(account) {
    const initialBalance = parseNumber(account.initial_balance);
    const currentBalance = parseNumber(account.current_balance);

    const totalProfit = currentBalance - initialBalance;

    const totalReturnPercent =
        initialBalance === 0
            ? 0
            : (totalProfit / initialBalance) * 100;

    return {
        initialBalance,
        currentBalance,
        totalProfit,
        totalReturnPercent,
        updatedAt: account.updated_at,
    };
}

function formatTrade(trade) {
    if (!trade) {
        return null;
    }

    return {
        id: trade.id,
        symbol: trade.symbol,
        direction: trade.direction,
        entryTime: trade.entry_time,
        entryPrice: parseNumber(trade.entry_price),
        exitTime: trade.exit_time,
        exitPrice: parseNumber(trade.exit_price),
        holdingCandles: trade.holding_candles,
        candlesRemaining: trade.candles_remaining,
        confidence: parseNumber(trade.confidence),
        modelVersion: trade.model_version,
        status: trade.status,
        grossReturnPercent: parseNumber(
            trade.gross_return_percent
        ),
        netReturnPercent: parseNumber(
            trade.net_return_percent
        ),
        positionSize: parseNumber(trade.position_size),
        pnlAmount: parseNumber(trade.pnl_amount),
        balanceAfter: parseNumber(trade.balance_after),
        createdAt: trade.created_at,
    };
}

async function getAccount() {
    const account = await database.get(
        `
        SELECT *
        FROM account
        WHERE id = 1
        `
    );

    if (!account) {
        throw new Error("Den virtuelle konto findes ikke.");
    }

    return formatAccount(account);
}

async function getOpenTrade() {
    const trade = await database.get(
        `
        SELECT *
        FROM trades
        WHERE status = 'OPEN'
        ORDER BY id DESC
        LIMIT 1
        `
    );

    return formatTrade(trade);
}

async function getStatistics() {
    const trades = await database.all(
        `
        SELECT net_return_percent
        FROM trades
        WHERE status = 'CLOSED'
          AND net_return_percent IS NOT NULL
        ORDER BY id ASC
        `
    );

    const returns = trades.map((trade) =>
        Number(trade.net_return_percent)
    );

    if (returns.length === 0) {
        return {
            totalTrades: 0,
            winningTrades: 0,
            losingTrades: 0,
            breakEvenTrades: 0,
            winRatePercent: 0,
            totalNetReturnPercent: 0,
            averageNetReturnPercent: 0,
            bestTradePercent: 0,
            worstTradePercent: 0,
            profitFactor: null,
        };
    }

    const winningReturns = returns.filter(
        (tradeReturn) => tradeReturn > 0
    );

    const losingReturns = returns.filter(
        (tradeReturn) => tradeReturn < 0
    );

    const breakEvenReturns = returns.filter(
        (tradeReturn) => tradeReturn === 0
    );

    const totalNetReturnPercent = returns.reduce(
        (sum, tradeReturn) => sum + tradeReturn,
        0
    );

    const grossProfit = winningReturns.reduce(
        (sum, tradeReturn) => sum + tradeReturn,
        0
    );

    const grossLoss = Math.abs(
        losingReturns.reduce(
            (sum, tradeReturn) => sum + tradeReturn,
            0
        )
    );

    return {
        totalTrades: returns.length,
        winningTrades: winningReturns.length,
        losingTrades: losingReturns.length,
        breakEvenTrades: breakEvenReturns.length,
        winRatePercent:
            (winningReturns.length / returns.length) * 100,
        totalNetReturnPercent,
        averageNetReturnPercent:
            totalNetReturnPercent / returns.length,
        bestTradePercent: Math.max(...returns),
        worstTradePercent: Math.min(...returns),
        profitFactor:
            grossLoss === 0
                ? null
                : grossProfit / grossLoss,
    };
}

app.get("/api/account", async (request, response) => {
    try {
        const account = await getAccount();

        response.json(account);
    } catch (error) {
        console.error(error);

        response.status(500).json({
            error: "Kunne ikke hente kontoen.",
        });
    }
});

app.get("/api/trade/open", async (request, response) => {
    try {
        const trade = await getOpenTrade();

        response.json({
            trade,
        });
    } catch (error) {
        console.error(error);

        response.status(500).json({
            error: "Kunne ikke hente den åbne handel.",
        });
    }
});

app.get("/api/trades", async (request, response) => {
    try {
        const limit = Math.min(
            Math.max(
                Number.parseInt(request.query.limit, 10) || 50,
                1
            ),
            500
        );

        const trades = await database.all(
            `
            SELECT *
            FROM trades
            ORDER BY id DESC
            LIMIT ?
            `,
            limit
        );

        response.json({
            count: trades.length,
            trades: trades.map(formatTrade),
        });
    } catch (error) {
        console.error(error);

        response.status(500).json({
            error: "Kunne ikke hente handler.",
        });
    }
});

app.get("/api/equity", async (request, response) => {
    try {
        const points = await database.all(
            `
            SELECT *
            FROM equity_history
            ORDER BY id ASC
            `
        );

        response.json({
            count: points.length,
            points: points.map((point) => ({
                id: point.id,
                tradeId: point.trade_id,
                timestamp: point.timestamp,
                balance: parseNumber(point.balance),
                totalProfit: parseNumber(
                    point.total_profit
                ),
                totalReturnPercent: parseNumber(
                    point.total_return_percent
                ),
            })),
        });
    } catch (error) {
        console.error(error);

        response.status(500).json({
            error: "Kunne ikke hente equity-historikken.",
        });
    }
});

app.get("/api/statistics", async (request, response) => {
    try {
        const statistics = await getStatistics();

        response.json(statistics);
    } catch (error) {
        console.error(error);

        response.status(500).json({
            error: "Kunne ikke beregne statistik.",
        });
    }
});

app.get("/api/status", async (request, response) => {
    try {
        const [
            account,
            openTrade,
            statistics,
            latestCandle,
        ] = await Promise.all([
            getAccount(),
            getOpenTrade(),
            getStatistics(),
            database.get(
                `
                SELECT *
                FROM candles
                ORDER BY open_time DESC
                LIMIT 1
                `
            ),
        ]);

        response.json({
            account,
            openTrade,
            statistics,
            market: latestCandle
                ? {
                    symbol: latestCandle.symbol,
                    interval: latestCandle.interval,
                    openTime: latestCandle.open_time,
                    closeTime: latestCandle.close_time,
                    open: parseNumber(
                        latestCandle.open_price
                    ),
                    high: parseNumber(
                        latestCandle.high_price
                    ),
                    low: parseNumber(
                        latestCandle.low_price
                    ),
                    close: parseNumber(
                        latestCandle.close_price
                    ),
                    volume: parseNumber(
                        latestCandle.volume
                    ),
                }
                : null,
        });
    } catch (error) {
        console.error(error);

        response.status(500).json({
            error: "Kunne ikke hente systemstatus.",
        });
    }
});


async function startServer() {
    try {
        database = await open({
            filename: DATABASE_PATH,
            driver: sqlite3.Database,
        });

        await database.get("SELECT 1");

        app.listen(PORT, () => {
            console.log(
                `AI Trading API kører på http://localhost:${PORT}`
            );

            console.log(
                `Database: ${DATABASE_PATH}`
            );
        });
    } catch (error) {
        console.error(
            "Kunne ikke starte serveren:",
            error
        );

        process.exit(1);
    }
}

startServer();
