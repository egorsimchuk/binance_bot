import webbrowser

from src.analysis.analyse import AssetAnalyser, OrdersAnalyser, generate_asset_table
from src.client.client import ClientHelper
import pandas as pd
import time
from datetime import datetime

from src.constants import remove_from_plots
from src.data.dump_data import dump_orders_data, DATA_FOLDER
from src.utils.utils import get_html_body_from_plotly_figure
import logging
logger = logging.getLogger(__name__)

REPORT_FOLDER = DATA_FOLDER / 'html_reports'

def make_report(api_key: str, api_secret: str, open_file: bool):
    start = time.time()
    client_helper = ClientHelper(api_key, api_secret)
    current_prices = client_helper.query_prices()

    orders = client_helper.get_all_orders()
    dump_orders_data(orders)

    order_analyser = OrdersAnalyser(client_helper, orders)

    portfolio_fig = order_analyser.plot_asset_usdt_composition(current_prices)

    asset_df = generate_asset_table(order_analyser, current_prices)

    history_assets = order_analyser.prepare_coins_asset_history()
    asset_history_long_fig = order_analyser.plot_full_asset_history(history_assets)

    coins = asset_df['base_coin']
    coins = [c for c in coins if c not in remove_from_plots]
    transactions_plots_dict = order_analyser.plot_transactions_many(coins)
    transactions_plots_html = ''
    for coin, fig in transactions_plots_dict.items():
        transactions_plots_html += get_html_body_from_plotly_figure(fig)

    fpath = generate_html_report(asset_df, portfolio_fig, asset_history_long_fig, transactions_plots_html, open_file=open_file)
    end = time.time()
    logger.info(f'HTML report executed for {round(end - start)} seconds')

    return fpath


def generate_html_report(mean_price, portfolio_fig, asset_history_long_fig, transactions_plots_html, open_file=False):
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
            ''' + get_html_body_from_plotly_figure(asset_history_long_fig) + '''
            ''' + "" + '''

            <h2>Section 2: Analysis of purchases</h2>

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
    logger.info(f'Report was saved at: {fpath}')

    if open_file:
        url = "file:///" + str(fpath)
        webbrowser.open(url, new=2)

    return fpath