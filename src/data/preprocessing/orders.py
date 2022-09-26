import logging
from typing import List

import pandas as pd

from src.client.client import ClientHelper
from src.data.preprocessing.base import BaseProcessor
from src.utils.utils import (cast_all_to_float, convert_timestamp_to_datetime,
                             load_config_json)

logger = logging.getLogger(__name__)


class OrdersProcessor(BaseProcessor):
    def __init__(
        self, client_helper: ClientHelper, divide_coin_convertion: bool = True
    ):
        """
        Args:
        currency_items: List of currencies for fetching.
            All possible pairs generated from that list.
            If None then default use currency_items from configs.
        divide_coin_convertion: Convert each coin-to-coin operation into 2 usdt operations - one for selling and
                                another for buying for usdt.

        """
        self.divide_coin_convertion = divide_coin_convertion
        self._client_helper = client_helper

    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Make transform of DataFrame wit order details
        Returns:
            Processed DataFrame with history of orders.
        """
        cast_all_to_float(data, except_columns=["time", "updateTime"])

        if self.divide_coin_convertion:
            data = self.divide_coin_convertion_into_usdt_operations(data)

        if len(data) > 0:
            data["date"] = data["time"].apply(convert_timestamp_to_datetime)
            data = data.sort_values("date").reset_index(drop=True)
        return data

    def divide_coin_convertion_into_usdt_operations(
        self, orders: pd.DataFrame, allowed_quote_coins: List[str] = None
    ):
        if allowed_quote_coins is None:
            allowed_quote_coins = ["USDT", "BUSD", "RUB"]
        transaction_coin = "USDT"
        pair_mask = orders["quote_coin"].isin(allowed_quote_coins)
        ok_orders = orders[pair_mask]
        div_orders = orders[~pair_mask]
        divided_orders = []

        for i, row in div_orders.iterrows():
            time = row["updateTime"]
            sell_row = row.copy()
            sell_symbol = row["quote_coin"] + transaction_coin
            candle = self._client_helper.get_aggregate_trades(
                symbol=sell_symbol, time=time
            )
            sell_row["symbol"] = sell_symbol
            sell_row["side"] = "SELL"
            sell_row["price"] = float(candle["p"])
            sell_row["base_coin"] = row["quote_coin"]
            sell_row["quote_coin"] = transaction_coin
            sell_row["cummulativeQuoteQty"] = (
                row["cummulativeQuoteQty"] * sell_row["price"]
            )
            sell_row["origQty"] = row["cummulativeQuoteQty"]
            sell_row["executedQty"] = row["cummulativeQuoteQty"]

            buy_row = row.copy()
            buy_symbol = row["base_coin"] + transaction_coin
            candle = self._client_helper.get_aggregate_trades(
                symbol=buy_symbol, time=time
            )

            buy_row["symbol"] = buy_symbol
            buy_row["price"] = float(candle["p"])
            buy_row["quote_coin"] = transaction_coin
            buy_row["cummulativeQuoteQty"] = row["executedQty"] * buy_row["price"]

            divided_orders.append(sell_row)
            divided_orders.append(buy_row)
        divided_orders = pd.DataFrame(divided_orders)
        orders = pd.concat([ok_orders, divided_orders])
        return orders
