from typing import Optional, Any, List

from binance.exceptions import BinanceAPIException
from binance import Client

from .binance_report import cast_all_to_float
from .utils import load_api_keys, load_json, convert_timestamp_to_datetime
import pandas as pd
import itertools
from multiprocessing.dummy import Pool as ThreadPool

MAX_ORDERS = 1000
PROCESSES_NUMBER = 15
RECV_WINDOW = 5000


class ClientHelper:

    def __init__(self):
        api_key, api_secret = load_api_keys()
        try:
            self.client = Client(api_key, api_secret)
        except BinanceAPIException as err:
            if err.code == -1003:
                err.message
            raise err('IP blocked until {convert_timestamp_to_datetime}')
        query_config = load_json('config/query.json')
        self.currency_items = query_config['orders_history']['currency_items']

    def query_pair_orders(self, currency_pair: list) -> Optional[Any]:
        """
        Query history of orders for currency pair
        Args:
            currency_pair: list with 2 names for base and quote currency

        Returns:
            List of dicts with order's info
        """
        pair_name = ''.join(currency_pair)
        try:
            orders = self.client.get_all_orders(symbol=pair_name, limit=MAX_ORDERS, recvWindow=RECV_WINDOW)
            if len(orders) == 0:
                return None
            for i in range(len(orders)):
                orders[i]['base_coin'] = currency_pair[0]
                orders[i]['quote_coin'] = currency_pair[1]

        except BinanceAPIException as e:
            if e.code == -1121:
                # Invalid symbol
                return None
            raise e

        return orders

    def get_all_orders(self, currency_items: list = None, divide_coin_convertion=True) -> pd.DataFrame:
        """
        Query history of orders for all possible combinations of currency pairs.

        Args:
            currency_items: List of currencies for fetching.
                All possible pairs generated from that list.
                If None then default use currency_items from configs.
            divide_coin_convertion: Convert each coin-to-coin operation into 2 usdt operations - one for selling and
                                    another for buying for usdt.

        Returns:
            Pandas DataFrame with history of orders.

        """
        if currency_items is None:
            currency_items = self.currency_items
        currency_combinations = itertools.permutations(currency_items, 2)

        with ThreadPool(PROCESSES_NUMBER) as pool:
            orders_lists = pool.map(self.query_pair_orders, currency_combinations)

        orders_lists = [o for o in orders_lists if o is not None]
        orders = list(itertools.chain.from_iterable(orders_lists))
        orders = pd.DataFrame(orders)
        cast_all_to_float(orders, except_columns=['time', 'updateTime'])

        if divide_coin_convertion:
            orders = self.divide_coin_convertion_into_usdt_operations(orders)

        if len(orders) > 0:
            orders['datetime'] = orders['time'].apply(convert_timestamp_to_datetime)
            orders = orders.sort_values('datetime').reset_index(drop=True)

        return orders

    def divide_coin_convertion_into_usdt_operations(self, orders: pd.DataFrame, allowed_quote_coins: List[str] = None):
        if allowed_quote_coins is None:
            allowed_quote_coins = ['USDT', 'BUSD', 'RUB']
        transaction_coin = 'USDT'
        pair_mask = orders['quote_coin'].isin(allowed_quote_coins)
        ok_orders = orders[pair_mask]
        div_orders = orders[~pair_mask]
        divided_orders = []

        for i, row in div_orders.iterrows():
            time = row['updateTime']
            sell_row = row.copy()
            sell_symbol = row['quote_coin'] + transaction_coin
            candle = self.client.get_aggregate_trades(symbol=sell_symbol, startTime=time, endTime=time + 1000, limit=1)[
                0]
            sell_row['symbol'] = sell_symbol
            sell_row['side'] = 'SELL'
            sell_row['price'] = float(candle['p'])
            sell_row['base_coin'] = row['quote_coin']
            sell_row['quote_coin'] = transaction_coin
            sell_row['cummulativeQuoteQty'] = row['cummulativeQuoteQty'] * sell_row['price']
            sell_row['origQty'] = row['cummulativeQuoteQty']
            sell_row['executedQty'] = row['cummulativeQuoteQty']

            buy_row = row.copy()
            buy_symbol = row['base_coin'] + transaction_coin
            candle = self.client.get_aggregate_trades(symbol=buy_symbol, startTime=time, endTime=time + 1000, limit=1)[
                0]
            buy_row['symbol'] = buy_symbol
            buy_row['price'] = float(candle['p'])
            buy_row['quote_coin'] = transaction_coin
            buy_row['cummulativeQuoteQty'] = row['executedQty'] * buy_row['price']

            divided_orders.append(sell_row)
            divided_orders.append(buy_row)
        divided_orders = pd.DataFrame(divided_orders)
        orders = pd.concat([ok_orders, divided_orders])
        return orders

    def query_asset(self, currency):
        """
        Query asset for selected currency.
        """
        return self.client.get_asset_balance(asset=currency)

    def get_all_assets(self, currency_items: list = None) -> pd.DataFrame:
        """
        Query assets for selected currencies.

        Args:
            currency_items: list of currencies for fetching.

        Returns:
            Pandas DataFrame with assets.

        """
        if currency_items is None:
            currency_items = self.currency_items

        with ThreadPool(PROCESSES_NUMBER) as pool:
            assets = pool.map(self.query_asset, currency_items)

        assets = [o for o in assets if len(o) > 0]

        assets = pd.DataFrame(assets)
        assets = assets.sort_values('asset').reset_index(drop=True)
        return assets

    def get_history_assets(self, trade_type: str = 'SPOT', days: int = 30):
        """
        Get daily history of asset. Asset's info is updated at 02:59:59 each day.

        Args:
            trade_type: Valid types SPOT/MARGIN/FUTURES.
            days: Length of history. Min is 5 and max is 30.

        Returns:
            Pandas DataFrame with history of asset.
        """
        df = self.client.get_account_snapshot(type=trade_type, limit=days)
        from src.utils import convert_timestamp_to_datetime
        df = pd.DataFrame(df['snapshotVos'])
        df['updateTime'] = df['updateTime'].apply(convert_timestamp_to_datetime)
        df['totalAssetOfBtc'] = pd.DataFrame([d['totalAssetOfBtc'] for d in df['data'].values])
        balances = [d['balances'] for d in df['data'].values]
        balances_ = []
        for balance in balances:
            asset = {d['asset']: (d['free'] + d['locked']) for d in balance}
            balances_.append(asset)
        balances_ = pd.DataFrame(balances_)
        balances = pd.concat([df.drop('data', axis=1), balances_], axis=1)
        return balances
