import pandas as pd
from binance.exceptions import BinanceAPIException

from src.client.client import ClientHelper
from src.data.dump_data import DUMP_PRICES_FPATH


def get_prices(client_helper: ClientHelper, start_date='1 Jan, 2021'):
    if DUMP_PRICES_FPATH.exists():
        price_history_old = pd.read_csv(DUMP_PRICES_FPATH, parse_dates=['date'])
        last_time = price_history_old.iloc[-1]['date'].strftime("%Y-%m-%d")
        start_date = last_time

    currency_items = client_helper.currency_items
    price_history_new = []

    for base_coin in currency_items:
        try:
            price_history = client_helper.get_historical_prices(base_coin + 'USDT', start_date=start_date)
            price_history = price_history[['Close', 'date']].set_index('date')
            price_history.columns = [base_coin]
            price_history_new.append(price_history)
        except BinanceAPIException:
            print(f'Can not get prices for {base_coin}')

    price_history_new = pd.concat(price_history_new, axis=1).reset_index()
    new_lines = len(price_history_new)

    if DUMP_PRICES_FPATH.exists():
        price_history_new = pd.concat([price_history_old.iloc[:-1], price_history_new])

    price_history_new.to_csv(DUMP_PRICES_FPATH, index=False)
    print(f'Prices dump was updated with {new_lines} new lines (days): {DUMP_PRICES_FPATH}')
    return price_history_new