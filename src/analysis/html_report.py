from src.analysis.analyse import AssetAnalyser, OrdersAnalyser
from src.client.client import ClientHelper
import pandas as pd
import time
from datetime import datetime

from src.data.dump_data import dump_orders_data, DATA_FOLDER
from src.utils.utils import get_html_body_from_plotly_figure
REPORT_FOLDER = DATA_FOLDER / 'html_reports'

def make_report(api_key, api_secret):
    start = time.time()

    client_helper = ClientHelper(api_key, api_secret)

    current_prices = client_helper.query_prices()
    history_assets = client_helper.get_history_assets('SPOT')
    asset_analyser = AssetAnalyser(client_helper)

    portfolio_fig = asset_analyser.plot_asset_composition_in_usdt(history_assets, current_prices)
    asset_history_fig = asset_analyser.plot_asset_usdt_value_history(history_assets)

    orders = client_helper.get_all_orders()
    dump_orders_data(orders)

    order_analyser = OrdersAnalyser(client_helper, orders)
    mean_price = order_analyser.calculate_mean_price()
    mean_price = pd.merge(mean_price, current_prices.rename(columns={'price': 'current_price'}),
                          on=['base_coin', 'quote_coin'], how='left')
    mean_price['price_change_usd'] = mean_price['current_price'] - mean_price['average_price']
    mean_price['price_change_percent'] = mean_price['price_change_usd'] / mean_price['average_price'] * 100

    coins = mean_price['base_coin']
    coins = [c for c in coins if c not in ['USDT']]
    transactions_plots_dict = order_analyser.plot_transactions_many(coins)
    transactions_plots_html = ''
    for coin, fig in transactions_plots_dict.items():
        transactions_plots_html += get_html_body_from_plotly_figure(fig)

    generate_html_report(mean_price, portfolio_fig, asset_history_fig, transactions_plots_html)
    end = time.time()
    print(f'Executed for {round(end - start)} seconds')


def generate_html_report(mean_price, portfolio_fig, asset_history_fig, transactions_plots_html):
    now_datetime = datetime.now()

    mean_price_table = mean_price.round(3).to_html().replace('<table border="1" class="dataframe">',
                                                             '<table class="table table-striped">')  # use bootstrap styling

    html_string = '''
    <html>
        <head>
            <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.1/css/bootstrap.min.css">
            <style>body{ margin:0 100; background:white; }</style>
            <script type="text/javascript" src="https://cdn.plot.ly/plotly-latest.min.js"></script></head>
        </head>
        <body>
            <h1>Binance profile report at ''' + now_datetime.strftime("%Y-%m-%d %H:%M") + '''</h1>

            <h2>Section 1: Asset composition</h2>
            ''' + get_html_body_from_plotly_figure(portfolio_fig) + '''
            ''' + get_html_body_from_plotly_figure(asset_history_fig) + '''
            ''' + "" + '''

            <h2>Analysis of purchases</h2>

            <h3>Average purchase price and benefits compared to current price</h3>
            ''' + mean_price_table + '''
            <h3>Transactions history</h3>
            ''' + transactions_plots_html + '''

        </body>
    </html>'''

    now_time = now_datetime.strftime('%Y-%m-%d_%Hh%Mm')
    REPORT_FOLDER.mkdir(exist_ok=True, parents=True)
    fpath = REPORT_FOLDER / f'{now_time}.html'
    f = open(fpath, 'w')
    f.write(html_string)
    f.close()
    print(f'Report was saved at: {fpath}')
