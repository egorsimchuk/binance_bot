import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.client import ClientHelper

QUOTE_COINS = ['USDT', 'BUSD']


class OrdersAnalyser:

    def __init__(self, orders):
        self.orders = self.prepare_dataframe(orders)

    @staticmethod
    def prepare_dataframe(orders: pd.DataFrame):
        orders = orders.copy()
        numerical_columns = ['price', 'origQty', 'executedQty', 'cummulativeQuoteQty']
        for col in numerical_columns:
            orders[col] = orders[col].astype(float)
        # Use only filled orders
        orders = orders[orders['status'] == 'FILLED']
        # Replace payments with BUSD to USDT to simplify
        orders.loc[orders['quote_coin'] == 'BUSD', 'quote_coin'] = 'USDT'
        return orders

    def calculate_mean_price(self, side: str = 'BUY'):
        orders = self.orders[self.orders['side'] == side]

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

    def plot_transactions(self, base_coin: str = 'BTC', price_history: pd.DataFrame = None,
                          add_mean_price: bool = True, add_last_price: bool = True):
        plot_df = self.orders[self.orders['base_coin'] == base_coin]
        assert np.all(
            np.isin(plot_df['quote_coin'].unique(), QUOTE_COINS)), f'Only {QUOTE_COINS} quote coins are acceptable'
        fig = px.scatter(plot_df, x='date', y="price", size='executedQty', color='side',
                         title=f'{base_coin} transactions', size_max=10, hover_data=['cummulativeQuoteQty'])
        if price_history is not None:
            fig.add_trace(
                go.Scatter(x=price_history['date'], y=price_history['Close'], mode='lines', name='history',
                           marker_color='grey'))

        if add_mean_price:
            mean_price = self.calculate_mean_price()
            mean_price = mean_price.loc[mean_price['base_coin'] == base_coin, 'average_price'].item()
            fig.add_hline(y=mean_price, line_dash="dot",
                          annotation_text=f'average purchase price = {round(mean_price, 1)} usdt',
                          annotation_position="bottom right")

        if add_last_price:
            last_price = price_history.iloc[-1]
            fig.add_annotation(
                x=last_price['date'],
                y=last_price['Close'],
                text=f"Last price = {round(last_price['Close'], 1)} usdt",
                arrowhead=2,
            )
        return fig


class AssetAnalyser:

    def plot_asset_composition_in_usdt(self, history_assets: pd.DataFrame, prices: pd.DataFrame) -> go.Figure:
        """
        Plot the most actual composition of asset in usdt.

        Args:
            history_assets: Table with columns ['type', 'date', 'totalAssetOfBtc', all coins in asset].
            prices: Table with columns ['price', 'base_coin', 'quote_coin'].

        Returns:

        """
        plot_df = history_assets.drop(['type', 'totalAssetOfBtc'], axis=1)
        labels = plot_df
        labels = [c for c in labels if c not in ['RUB', 'date']]
        values = plot_df[labels].iloc[-1]
        for i, coin in enumerate(labels):
            price = prices.loc[prices['base_coin'] == coin, 'price'].item()
            values[i] *= price
        fig = go.Figure(data=[go.Pie(labels=labels, values=values.round(), textinfo='label', )])
        fig.update_layout(title=f'Asset composition in usdt. Total value = {np.sum(values).round(1)} usdt.', autosize=False, width=500, height=500)
        return fig
