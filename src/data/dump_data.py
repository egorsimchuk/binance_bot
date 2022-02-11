import pandas as pd

from src.utils.utils import get_project_dir
DATA_FOLDER = get_project_dir() / 'data'
DUMP_FOLDER = DATA_FOLDER / 'dumps'
DUMP_ORDERS_FPATH = DUMP_FOLDER / 'orders_dump.csv'

def load_orders_data():
    orders = pd.read_csv(DUMP_ORDERS_FPATH, parse_dates=['date'])
    return orders

def dump_orders_data(orders: pd.DataFrame):
    DUMP_FOLDER.mkdir(exist_ok=True, parents=True)
    if DUMP_ORDERS_FPATH.exists():
        orders_old = load_orders_data()
        mask_new = ~orders.date.apply(lambda t: t in orders_old.date.values)
        new_orders = pd.concat([orders_old, orders[mask_new]], axis=0)
    else:
        new_orders = orders

    new_orders.to_csv(DUMP_ORDERS_FPATH, index=False)
    print(f'Orders dump was updated: {DUMP_ORDERS_FPATH}')