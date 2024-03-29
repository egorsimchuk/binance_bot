import itertools
import logging
from multiprocessing.dummy import Pool as ThreadPool
from time import sleep
from typing import Any, Dict, List, Optional

import pandas as pd
from binance import Client
from binance.exceptions import BinanceAPIException

from src.utils.utils import (cast_all_to_float, convert_timestamp_to_datetime,
                             load_config_json)

logger = logging.getLogger(__name__)
MAX_ORDERS = 1000
PROCESSES_NUMBER = 15
RECV_WINDOW = 5000
KLINES_COLUMNS = [
    "Open time",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "Close time",
    "Quote asset volume",
    "Number of trades",
    "Taker buy base asset volume",
    "Taker buy quote asset volume",
    "Can be ignored",
]


class ClientHelper:
    def __init__(self, api_key: str, api_secret: str):
        self.client: Client = None
        try:
            self.client = Client(api_key, api_secret)
        except BinanceAPIException as err:
            if err.code == -1003:
                err.message
                # raise err(f'IP blocked until {convert_timestamp_to_datetime}')
            raise err
        query_config = load_config_json("config/query.json")
        self._currency_items = query_config["orders_history"]["currency_items"]
        logger.info(f"fetching coins: {self.currency_items}")

    @property
    def currency_items(self):
        return self._currency_items

    @currency_items.setter
    def currency_items(self, value):
        self._currency_items = value

    def _query_pair_orders(self, currency_pair: list) -> Optional[List[Any]]:
        """
        Query history of orders for currency pair
        Args:
            currency_pair: list with 2 names for base and quote currency

        Returns:
            List of dicts with order's info
        """
        pair_name = "".join(currency_pair)
        try:
            orders = self.client.get_all_orders(
                symbol=pair_name, limit=MAX_ORDERS, recvWindow=RECV_WINDOW
            )
            if len(orders) == 0:
                return None
            for i in range(len(orders)):
                orders[i]["base_coin"] = currency_pair[0]
                orders[i]["quote_coin"] = currency_pair[1]

        except BinanceAPIException as e:
            if e.code == -1121:
                # Invalid symbol
                return None
            raise e

        orders = self._fill_price_for_market_price_transaction(orders)
        return orders

    def _fill_price_for_market_price_transaction(
        self, orders: Optional[List[Any]]
    ) -> Optional[List[Any]]:
        if len(orders) == 0:
            return orders

        for i in range(len(orders)):
            order = orders[i]
            if order["type"] == "MARKET":
                order["price"] = self._get_timestamp_price(
                    order["symbol"], order["time"]
                )

        return orders

    def load_orders(self):
        """
        Query history of orders for all possible combinations of currency pairs.

        Args:
            currency_items: List of currencies for fetching.
                All possible pairs generated from that list.
                If None then default use currency_items from configs.
        Returns:
            DataFrame with orders details
        """
        currency_combinations = list(itertools.permutations(self.currency_items, 2))
        # bypass protection. Avoid APIError(code=-1003): Too much request weight used
        n_batches = 3
        batch_size = len(currency_combinations) // n_batches
        orders_lists = []
        for i in range(n_batches + 1):
            logger.info(f"Avoid APIError(code=-1003), batch {i}")
            while True:
                try:
                    with ThreadPool(PROCESSES_NUMBER) as pool:
                        orders_lists.extend(
                            pool.map(
                                self._query_pair_orders,
                                currency_combinations[
                                    i * batch_size: i * batch_size + batch_size
                                ],
                            )
                        )
                    break
                except BinanceAPIException as ex:
                    logger.warning(ex.message)
                    logger.info("Avoid APIError(code=-1003), sleep extra 60 seconds")
                    sleep(60)
            sleep(10)

        orders_lists = [o for o in orders_lists if o is not None]
        orders = list(itertools.chain.from_iterable(orders_lists))
        return pd.DataFrame(orders)

    def _query_asset(self, currency):
        """
        Query asset for selected currency.
        """
        return self.client.get_asset_balance(asset=currency)

    def get_all_assets(self) -> pd.DataFrame:
        """
        Query assets for selected currencies.
        Returns:
            Pandas DataFrame with assets.

        """
        with ThreadPool(PROCESSES_NUMBER) as pool:
            assets = pool.map(self._query_asset, self.currency_items)

        assets = [o for o in assets if len(o) > 0]

        assets = pd.DataFrame(assets)
        assets = assets.sort_values("asset").reset_index(drop=True)
        return assets

    def get_history_assets(self, trade_type: str = "SPOT", days: int = 30):
        """
        Get daily history of asset. Asset's info is updated at 02:59:59 each day.

        Args:
            trade_type: Valid types SPOT/MARGIN/FUTURES.
            days: Length of history. Min is 5 and max is 30.

        Returns:
            Pandas DataFrame with history of asset.
        """
        df = self.client.get_account_snapshot(type=trade_type, limit=days)
        df = pd.DataFrame(df["snapshotVos"])
        df["date"] = df["updateTime"].apply(
            convert_timestamp_to_datetime
        ) + pd.Timedelta(seconds=1)
        df = df.drop("updateTime", axis=1)
        df["totalAssetOfBtc"] = pd.DataFrame(
            [d["totalAssetOfBtc"] for d in df["data"].values]
        )
        balances = [d["balances"] for d in df["data"].values]
        balances_ = []
        for balance in balances:
            asset = {d["asset"]: (d["free"] + d["locked"]) for d in balance}
            balances_.append(asset)
        balances_ = pd.DataFrame(balances_)
        balances = pd.concat([df.drop("data", axis=1), balances_], axis=1)

        # get rid of extra points in asset quantity, i.e. usdt count may be 724.15828343149.8
        for c in ["RUB", "USDT"]:
            balances[c] = balances[c].apply(lambda x: x[:-4])
        cast_all_to_float(balances, except_columns=["date"])

        return balances

    def _get_timestamp_price(self, coin_pair, timestamp):
        data = self.client.get_historical_klines(
            coin_pair,
            Client.KLINE_INTERVAL_1MINUTE,
            start_str=timestamp,
            end_str=int(timestamp + 60 * 1e3),
        )
        data = dict(zip(KLINES_COLUMNS, data[0]))
        return float(data["Close"])

    def get_historical_prices(self, coin_pair, start_date="1 Jan, 2020"):
        data = self.client.get_historical_klines(
            coin_pair, Client.KLINE_INTERVAL_1DAY, start_date, limit=1000
        )
        data = pd.DataFrame(data, columns=KLINES_COLUMNS)
        cast_all_to_float(data)
        data["date"] = data["Open time"].apply(convert_timestamp_to_datetime)
        return data

    def query_prices(self):
        prices = self.client.get_all_tickers()
        prices = pd.DataFrame(prices)
        cast_all_to_float(prices)
        main_currency = "USDT"
        prices = prices[
            prices["symbol"].apply(lambda x: x[-len(main_currency):] == main_currency)
        ]
        prices["base_coin"] = prices["symbol"].apply(lambda x: x[: -len(main_currency)])
        prices["quote_coin"] = main_currency
        prices = prices.drop("symbol", axis=1)
        # add BETH price
        eth_price = prices.loc[prices["base_coin"] == "ETH", "price"].item()
        prices = pd.concat(
            [
                prices,
                pd.DataFrame(
                    [{"price": eth_price, "base_coin": "BETH", "quote_coin": "USDT"}]
                ),
            ]
        )
        # add USDT itself price
        prices["price"] = prices["price"].astype(float)
        prices = pd.concat(
            [
                prices,
                pd.DataFrame([{"price": 1, "base_coin": "USDT", "quote_coin": "USDT"}]),
            ]
        )
        return prices

    def get_aggregate_trades(self, symbol: str, time: int) -> Dict[str, Any]:
        window_ms = 1000  # aggregate trades in 1 second window for a start
        while True:
            try:
                return self.client.get_aggregate_trades(
                    symbol=symbol, startTime=time, endTime=time + window_ms, limit=1
                )[0]
            except IndexError:
                window_ms *= 2  # double the window size if no trades are found
                if window_ms > 300000:
                    logger.warning(f"Windows size exceed 5 minutes in get_candle")
                continue
