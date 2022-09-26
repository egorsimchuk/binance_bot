import logging

import pandas as pd
from binance.exceptions import BinanceAPIException

from src.client.client import ClientHelper
from src.data.dump_data import DUMP_PRICES_FPATH

logger = logging.getLogger(__name__)

START_PRICES_DATE = "2017-01-01"
COINS_PRICE_MATCHES = {"BETH": "ETH"}


def get_prices(client_helper: ClientHelper, start_date=START_PRICES_DATE):
    if DUMP_PRICES_FPATH.exists():
        price_history_old = pd.read_csv(DUMP_PRICES_FPATH, parse_dates=["date"])
        last_time = price_history_old.iloc[-1]["date"].strftime("%Y-%m-%d")
        start_date = last_time

    currency_items = client_helper.currency_items
    price_history_new = []

    for base_coin in currency_items:
        try:
            base_coin_ = (
                COINS_PRICE_MATCHES[base_coin]
                if base_coin in COINS_PRICE_MATCHES
                else base_coin
            )
            price_history = client_helper.get_historical_prices(
                base_coin_ + "USDT", start_date=start_date
            )
            price_history = price_history[["Close", "date"]].set_index("date")
            price_history.columns = [base_coin]
            price_history_new.append(price_history)
        except BinanceAPIException:
            logger.info(f"Can not get prices for {base_coin}")

    price_history_new = pd.concat(price_history_new, axis=1).reset_index()
    new_lines = len(price_history_new)

    if DUMP_PRICES_FPATH.exists():
        price_history_new = pd.concat([price_history_old.iloc[:-1], price_history_new])

    price_history_new.to_csv(DUMP_PRICES_FPATH, index=False)
    logger.info(
        f"Prices dump was updated with {new_lines} new lines (days): {DUMP_PRICES_FPATH}"
    )
    return price_history_new


def round_price(value: float) -> float:
    if value > 100:
        ndigits = 1
    elif value > 1:
        ndigits = 2
    else:
        ndigits = 4
    return round(value, ndigits)
