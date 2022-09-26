import logging
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.constants import remove_from_plots
from src.data.prices import get_prices, round_price
from src.plot.asset_history import plot_asset_history

logger = logging.getLogger(__name__)

QUOTE_COINS = ["USDT", "BUSD", "RUB"]


class OrdersAnalyser:
    def __init__(self, client_helper, orders):
        self._orders = self.prepare_dataframe(orders)
        self.client_helper = client_helper
        self.width = 1200
        self.height = 400

    @property
    def orders(self):
        return self._orders

    @staticmethod
    def prepare_dataframe(orders: pd.DataFrame):
        orders = orders.copy()
        numerical_columns = ["price", "origQty", "executedQty", "cummulativeQuoteQty"]
        for col in numerical_columns:
            orders[col] = orders[col].astype(float)
        # Use only filled orders
        orders = orders[orders["status"] == "FILLED"]
        # Replace payments with BUSD to USDT to simplify
        orders.loc[orders["quote_coin"] == "BUSD", "quote_coin"] = "USDT"
        # Calculate executedCorrectedQty, needed for calculation mean buying price
        updated_orders = []
        for _, pair_orders in orders.groupby(["base_coin"]):
            updated_orders.append(calculate_corrected_balance_for_pair(pair_orders))
        orders = pd.concat(updated_orders)

        assert np.all(
            np.isin(orders["quote_coin"].unique(), QUOTE_COINS)
        ), f"Only {QUOTE_COINS} quote coins allowed"
        return orders

    def calculate_mean_price(self):
        orders = self._orders

        average_prices = []
        for base_coin, pair_orders in orders.groupby(["base_coin"]):
            quote_coin = pair_orders["quote_coin"].unique()
            if len(quote_coin) > 1:
                msg = (
                    f"can calculate average purchase price only with single quote_coin, "
                    f"but for {base_coin} there is several: {quote_coin}"
                )
                raise ValueError(msg)
            quote_coin = quote_coin[0]
            mask_buy = pair_orders["side"] == "BUY"
            average_price = (
                pair_orders.loc[mask_buy, "price"]
                * pair_orders.loc[mask_buy, "executedCorrectedQty"]
            ).sum() / pair_orders.loc[mask_buy, "executedCorrectedQty"].sum()
            average_prices.append(
                {
                    "base_coin": base_coin,
                    "quote_coin": quote_coin,
                    "average_price": average_price,
                    "n_purchases": mask_buy.sum(),
                    "n_sales": (~mask_buy).sum(),
                }
            )
        average_prices = pd.DataFrame(average_prices)

        return average_prices

    def plot_transactions(
        self,
        base_coin: str = "BTC",
        price_history: pd.DataFrame = None,
        add_mean_price: bool = True,
        add_last_price: bool = True,
    ):
        plot_df = self.orders[self.orders["base_coin"] == base_coin]
        assert np.all(
            np.isin(plot_df["quote_coin"].unique(), QUOTE_COINS)
        ), f"Only {QUOTE_COINS} quote coins are acceptable"
        fig = px.scatter(
            plot_df,
            x="date",
            y="price",
            size="executedQty",
            color="side",
            title=f"{base_coin} transactions",
            size_max=10,
            hover_data=["cummulativeQuoteQty"],
        )
        if price_history is not None:
            fig.add_trace(
                go.Scatter(
                    x=price_history["date"],
                    y=price_history["Close"],
                    mode="lines",
                    name="history",
                    marker_color="grey",
                )
            )

        if add_mean_price:
            mean_price = self.calculate_mean_price()
            mean_price = mean_price.loc[
                mean_price["base_coin"] == base_coin, "average_price"
            ].item()
            fig.add_hline(
                y=mean_price,
                line_dash="dot",
                annotation_text=f"average purchase price = {round_price(mean_price)} usdt",
                annotation_position="bottom right",
            )

        if add_last_price:
            last_price = price_history.iloc[-1]
            fig.add_annotation(
                x=last_price["date"],
                y=last_price["Close"],
                text=f"Last price = {round_price(last_price['Close'])} usdt",
                arrowhead=2,
            )
        fig.update_xaxes(
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list(
                    [
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(count=6, label="6m", step="month", stepmode="backward"),
                        dict(count=1, label="1y", step="year", stepmode="backward"),
                        dict(step="all"),
                    ]
                )
            ),
            type="date",
        )
        fig.update_layout(
            yaxis_title="USDT",
            width=self.width,
            height=self.height,
            xaxis_fixedrange=False,
            yaxis_fixedrange=False,
        )

        return fig

    def plot_transactions_many(self, coins):
        fig_dict = {}
        for base_coin in coins:  # ['LTC', 'ETH']:
            price_history = self.client_helper.get_historical_prices(
                base_coin + "USDT", start_date="1 Jan, 2021"
            )
            fig = self.plot_transactions(base_coin, price_history)
            fig_dict[base_coin] = fig
        return fig_dict

    def prepare_coins_asset_history(self) -> Dict[str, pd.DataFrame]:
        coins_asset_history = {}
        prices = get_prices(self.client_helper)
        for base_coin, pair_orders in self.orders.groupby("base_coin"):
            if base_coin in remove_from_plots:
                continue
            price_history = prices[["date", base_coin]]
            price_history.columns = ["date", "price"]
            asset_history = calculate_asset_worth_history(pair_orders, price_history)
            coins_asset_history[base_coin] = asset_history
        return coins_asset_history

    def plot_coins_asset_history(
        self, coins_asset_history: Dict[str, pd.DataFrame], items: Optional[List] = None
    ):
        fig_dict = {}
        if items is None:
            items = coins_asset_history.keys()
        for item in items:
            plot_df = coins_asset_history[item]
            fig = plot_asset_history(
                plot_df,
                title=f"{item} asset value history",
                width=self.width,
                height=self.height,
            )
            fig_dict[item] = fig
        return fig_dict

    def plot_full_asset_history(
        self, coins_asset_history: Dict[str, pd.DataFrame], items: Optional[List] = None
    ):
        cash_df = []
        coin_df = []
        if items is None:
            items = coins_asset_history.keys()
        for item in items:
            plot_df = coins_asset_history[item]
            cash_df.append(plot_df[["date", "usdt_cash_in_cum"]].set_index("date"))
            coin_df.append(plot_df[["date", "coin_cum_usdt_value"]].set_index("date"))
        cash_df = pd.concat(cash_df, axis=1).ffill().sum(axis=1)
        cash_df.name = "usdt_cash_in_cum"
        coin_df = pd.concat(coin_df, axis=1).ffill().sum(axis=1)
        coin_df.name = "coin_cum_usdt_value"
        full_asset_history = pd.concat([cash_df, coin_df], axis=1).reset_index().ffill()
        fig = plot_asset_history(
            full_asset_history,
            title="Asset usdt value history",
            width=self.width,
            height=self.height,
        )
        return fig

    def asset_usdt_composition(self, prices: pd.DataFrame):
        asset_df = (
            self._orders[self._orders["side"] == "BUY"]
            .groupby("base_coin")["executedCorrectedQty"]
            .sum()
            .reset_index()
        )

        def convert_to_usd_price(
            raw,
        ):
            try:
                return (
                    raw["executedCorrectedQty"]
                    * prices.loc[
                        prices["base_coin"] == raw["base_coin"], "price"
                    ].item()
                )
            except ValueError:
                logger.info(
                    f'{raw["base_coin"]} coin is not listed in binance, price is not available'
                )
                return None

        asset_df["usdt_value"] = asset_df.apply(convert_to_usd_price, axis=1)
        asset_df = asset_df[asset_df["base_coin"] != "USDT"]
        return asset_df

    def plot_asset_usdt_composition(self, prices: pd.DataFrame):
        """
        Plot the most actual composition of asset in usdt.

        Args:
            history_assets: Table with columns ['type', 'date', 'totalAssetOfBtc', all coins in asset].
            prices: Table with columns ['price', 'base_coin', 'quote_coin'].

        Returns:

        """
        plot_df = self.asset_usdt_composition(prices)
        fig = px.pie(plot_df, values="usdt_value", names="base_coin")
        fig.update_layout(
            title=f'Asset composition in usdt. Total value = {plot_df["usdt_value"].sum().round(1)} usdt.',
            autosize=False,
            width=500,
            height=500,
        )
        return fig


def generate_asset_table(
    order_analyser: OrdersAnalyser, current_prices: pd.DataFrame
) -> pd.DataFrame:
    asset_df = order_analyser.calculate_mean_price()

    asset_df = pd.merge(
        asset_df,
        current_prices.rename(columns={"price": "current_price"}),
        on=["base_coin", "quote_coin"],
        how="left",
    )
    asset_df["price_change_usd"] = asset_df["current_price"] - asset_df["average_price"]
    asset_df["price_change_percent"] = (
        asset_df["price_change_usd"] / asset_df["average_price"] * 100
    )

    asset_df = pd.merge(
        asset_df,
        order_analyser.asset_usdt_composition(current_prices),
        how="outer",
        on="base_coin",
    )
    asset_df = asset_df.rename(columns={"executedCorrectedQty": "coins_count"})
    asset_df["usdt_share_percent"] = (
        asset_df["usdt_value"] / asset_df["usdt_value"].sum() * 100
    )
    return asset_df.sort_values("usdt_share_percent", ascending=False).reset_index(
        drop=True
    )


def calculate_corrected_balance_for_pair(pair_orders: pd.DataFrame):
    assert (
        len(pair_orders["base_coin"].unique()) == 1
    ), f'DataFrame should contain one base coin, but there are several: {pair_orders["base_coin"].unique()}'

    pair_orders["executedCorrectedQty"] = pair_orders[
        "executedQty"
    ]  # corrected coin quantity by selled tokens
    pair_orders["usdtValue"] = np.nan  # usdt value of buyed tokens
    pair_orders[
        "usdtValueCorrection"
    ] = np.nan  # delta correction usdt value of buyed tokens
    pair_orders.loc[
        pair_orders["side"] == "SELL", ["executedCorrectedQty", "usdtValue"]
    ] = None
    pair_orders["usdtQtyWeight"] = np.nan  # weights of buy orders in usdt terms
    pair_orders = pair_orders.reset_index(drop=True)
    cash_usdt_amount = 0
    for i in range(len(pair_orders)):
        mask_slice = pair_orders.index <= i
        mask_buy = pair_orders["side"] == "BUY"
        mask_slice_buy = mask_slice & mask_buy
        if pair_orders.loc[mask_slice, "side"].iloc[-1] == "SELL":
            pair_orders.loc[mask_slice_buy, "usdtValue"] = (
                pair_orders.loc[mask_slice_buy, "cummulativeQuoteQty"]
                * pair_orders.loc[mask_slice, "price"].iloc[-1]
                / pair_orders.loc[mask_slice_buy, "price"]
            )
            pair_orders.loc[mask_slice_buy, "usdtQtyWeight"] = (
                pair_orders.loc[mask_slice_buy, "usdtValue"]
                / pair_orders.loc[mask_slice_buy, "usdtValue"].sum()
            )
            sell_amount = pair_orders.loc[mask_slice, "cummulativeQuoteQty"].iloc[-1]
            pair_orders.loc[mask_slice_buy, "usdtValueCorrection"] = (
                sell_amount * pair_orders.loc[mask_slice_buy, "usdtQtyWeight"]
            )
            cash_usdt_amount += sell_amount
            # Reduce corrected coin quantity with ratio of decreased usdtValue from sell order
            if pair_orders.loc[mask_slice_buy, "executedCorrectedQty"].sum() == 0:
                raise ValueError(
                    "Bad balance error, looks like not all orders are listed. There are no coins available for selling"
                )
            # pair_orders.loc[mask_slice_buy, 'executedCorrectedQty'] -= pair_orders.loc[mask_slice_buy, 'usdtValueCorrection']/pair_orders.loc[mask_slice_buy, 'price']
            pair_orders.loc[mask_slice_buy, "executedCorrectedQty"] *= (
                1
                - pair_orders.loc[mask_slice_buy, "usdtValueCorrection"]
                / pair_orders.loc[mask_slice_buy, "usdtValue"]
            )
    pair_orders = pair_orders.drop(
        ["usdtValue", "usdtValueCorrection", "usdtQtyWeight"], axis=1
    )
    return pair_orders


def calculate_asset_worth_history(pair_orders, price_history):
    price_history = price_history.copy()
    pair_orders = pair_orders.apply(calc_transfers, axis=1)
    pair_orders["usdt_cash_in_cum"] = pair_orders["usdt_cash_transfer"].cumsum()
    pair_orders["coin_cum"] = pair_orders["coin_transfer"].cumsum()

    price_history.date = price_history.date.dt.to_period("D")

    asset_history = pair_orders[["date", "usdt_cash_in_cum", "coin_cum"]]
    asset_history_last_row = asset_history.iloc[0].copy()
    asset_history_last_row[:] = np.nan
    asset_history_last_row["date"] = pd.Timestamp(datetime.today().strftime("%Y-%m-%d"))
    asset_history = pd.concat([asset_history, asset_history_last_row.to_frame().T])

    asset_history = (
        asset_history.set_index("date")
        .resample("D", label="right", closed="right")
        .last()
        .ffill()
        .bfill()
        .reset_index()
    )

    asset_history.date = asset_history.date.dt.to_period("D")
    asset_history = pd.merge(asset_history, price_history, on="date", how="left")
    asset_history["coin_cum_usdt_value"] = (
        asset_history["coin_cum"] * asset_history["price"]
    )
    asset_history.date = asset_history.date.dt.to_timestamp()
    asset_history.date -= pd.Timedelta("1 day")

    return asset_history


def calc_transfers(row):
    if row["side"] == "BUY":
        row["usdt_cash_in"] = row["cummulativeQuoteQty"]
        row["usdt_cash_out"] = np.nan
        row["usdt_cash_transfer"] = row["cummulativeQuoteQty"]
        row["coin_transfer"] = row["executedQty"]

    else:
        row["usdt_cash_in"] = np.nan
        row["usdt_cash_out"] = row["cummulativeQuoteQty"]
        row["usdt_cash_transfer"] = -row["cummulativeQuoteQty"]
        row["coin_transfer"] = -row["executedQty"]
    return row


class AssetAnalyser:
    def __init__(self, client_helper):
        self.client_helper = client_helper
        self.width = 1200
        self.height = 400

    def plot_asset_composition_in_usdt(
        self, history_assets: pd.DataFrame, prices: pd.DataFrame
    ) -> go.Figure:
        """
        Plot the most actual composition of asset in usdt.

        Args:
            history_assets: Table with columns ['type', 'date', 'totalAssetOfBtc', all coins in asset].
            prices: Table with columns ['price', 'base_coin', 'quote_coin'].

        Returns:

        """
        plot_df = history_assets.drop(["type", "totalAssetOfBtc"], axis=1)
        labels = plot_df
        labels = [c for c in labels if c not in ["RUB", "date"]]
        values = plot_df[labels].iloc[-1]
        for i, coin in enumerate(labels):
            try:
                price = prices.loc[prices["base_coin"] == coin, "price"].item()
            except ValueError:
                logger.info(
                    f"{coin} coin is not listed in binance, price is not available"
                )
            values[i] *= price
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values.round(),
                    textinfo="label",
                )
            ]
        )
        fig.update_layout(
            title=f"Asset composition in usdt. Total value = {np.sum(values).round(1)} usdt.",
            autosize=False,
            width=500,
            height=500,
        )
        return fig

    def plot_asset_usdt_value_history(self, history_assets: pd.DataFrame) -> go.Figure:
        """
        Plot the history of usdt's value of asset.

        Args:
            history_assets: Table with columns ['type', 'date', 'totalAssetOfBtc', all coins in asset].

        Returns:

        """
        btc_price_history = self.client_helper.get_historical_prices(
            "BTCUSDT", start_date="1 Jan, 2021"
        )
        plot_df = history_assets.copy()
        plot_df = pd.merge(plot_df, btc_price_history[["Close", "date"]], on="date")
        plot_df["usdt value"] = plot_df["totalAssetOfBtc"] * plot_df["Close"]
        fig = px.line(plot_df, "date", "usdt value", title="Asset usdt value history")
        fig.update_layout(
            yaxis_title="USDT", autosize=False, width=self.width, height=self.height
        )
        return fig
