from src.client.client import ClientHelper
import logging
from src.utils.logging import log_format, log_level
logging.basicConfig(format=log_format, level=log_level)

if __name__ == '__main__':
    client = ClientHelper()
    client.get_all_orders()
