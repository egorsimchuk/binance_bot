from src.client.client import ClientHelper
from src.data.preprocessing.orders import OrdersProcessor


def load_and_process(client_helper: ClientHelper, data_processor: OrdersProcessor):
    """
    Load and process orders
    """
    data = client_helper.load_orders()
    data = data_processor.transform(data)
    return data
