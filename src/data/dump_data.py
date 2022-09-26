import logging

import pandas as pd

from src.utils.utils import get_project_dir

logger = logging.getLogger(__name__)

DATA_FOLDER = get_project_dir() / "data"
DUMP_FOLDER = DATA_FOLDER / "dumps"
DUMP_ORDERS_FPATH = DUMP_FOLDER / "orders_dump.csv"
DUMP_PRICES_FPATH = DUMP_FOLDER / "prices_dump.csv"


def load_orders_data():
    orders = pd.read_csv(DUMP_ORDERS_FPATH, parse_dates=["date"])
    return orders


def dump_orders_data(orders: pd.DataFrame):
    DUMP_FOLDER.mkdir(exist_ok=True, parents=True)
    new_lines = 0
    if DUMP_ORDERS_FPATH.exists():
        orders_old = load_orders_data()
        mask_new = ~orders.date.apply(lambda t: t in orders_old.date.values)
        new_orders = pd.concat([orders_old, orders[mask_new]], axis=0)
        new_lines = mask_new.sum()
    else:
        new_orders = orders

    new_orders.to_csv(DUMP_ORDERS_FPATH, index=False)
    logger.info(
        f"Orders dump was updated with {new_lines} new lines: {DUMP_ORDERS_FPATH}"
    )
    return new_orders
