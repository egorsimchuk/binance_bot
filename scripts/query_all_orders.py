import argparse

from src.client.client import ClientHelper
import logging

from src.data.orders_handler import load_and_process
from src.data.preprocessing.orders import OrdersProcessor
from src.utils.logging import log_format, log_level
logging.basicConfig(format=log_format, level=log_level)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('api_key', type=str, help='Key from binance profile')
    parser.add_argument('api_secret', type=str, help='Secret key from binance profile')
    parser.add_argument('open_file', type=int, nargs='?', default=1, choices=[0,1], help='Open html report after creating')
    args = parser.parse_args()
    client_helper = ClientHelper(args.api_key, args.api_secret)
    orders_processor = OrdersProcessor(client_helper=client_helper)
    data = load_and_process(client_helper, orders_processor)
    print(data.shape)
