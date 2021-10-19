import pandas as pd


class OrdersAnalyser:

    def __init__(self, orders):
        self.orders = self.prepare_dataframe(orders)

    @staticmethod
    def prepare_dataframe(orders):
        orders = orders.copy()
        numerical_columns = ['price', 'origQty', 'executedQty', 'cummulativeQuoteQty']
        for col in numerical_columns:
            orders[col] = orders[col].astype(float)
        # Use only filled orders
        orders = orders[orders['status'] == 'FILLED']
        # Replace payments with BUSD to USDT to simplify
        orders.loc[orders['quote_coin'] == 'BUSD', 'quote_coin'] = 'USDT'
        return orders

    def calculate_mean_price(self):
        orders = self.orders

        average_prices = []
        for base_coin, group in orders.groupby(['base_coin']):
            quote_coin = group['quote_coin'].unique()
            if len(quote_coin) > 1:
                msg = f'can calculate average purchase price only with single quote_coin, ' \
                      f'but for {base_coin} there is several: {quote_coin}'
                raise ValueError(msg)
            quote_coin = quote_coin[0]
            average_price = (group['price'] * group['executedQty']).sum() / group[
                'executedQty'].sum()
            average_prices.append(
                {'base_coin': base_coin, 'quote_coin': quote_coin, 'average_price': average_price,
                 'n_purchases': len(group)})
        average_prices = pd.DataFrame(average_prices)

        return average_prices
