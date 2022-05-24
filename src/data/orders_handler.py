from src.client.client import ClientHelper
from src.data.preprocessing.orders import OrdersProcessor


class OrdersHandler():
    """
    Load and process orders
    """

    def __init__(self, client_helper: ClientHelper, data_processor: OrdersProcessor):
        self.client_helper = client_helper
        self.data_processor = data_processor

    def load(self):
        data = self.client_helper.load_orders()
        data = self.data_processor.transform(data)
        return data
