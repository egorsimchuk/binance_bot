import json
import datetime
from pathlib import Path
from typing import List
import pandas as pd
from kaleido.scopes.plotly import PlotlyScope
from pathlib import Path

PLOT_CONVERTER = PlotlyScope()

try:
    from plotly.offline import plot
except ModuleNotFoundError:
    pass


def plotly_hide_traces_legend_without_name(fig):
    for trace in fig['data']:
        if trace['name'] is None: trace['showlegend'] = False


def get_html_body_from_plotly_figure(fig):
    return plot(fig, include_plotlyjs=False, output_type='div')


def convert_plotly_figure_to_html(fig):
    raw_html = '<html><head><meta charset="utf-8" />'
    raw_html += '<script type="text/javascript" src="https://cdn.plot.ly/plotly-latest.min.js"></script></head>'
    raw_html += '<body>'
    raw_html += get_html_body_from_plotly_figure(fig)
    raw_html += '</body></html>'
    return raw_html


def save_plot_with_external_script_link(fig, fpath, auto_open=False):
    raw_html = convert_plotly_figure_to_html(fig)
    with open(str(fpath), 'w') as text_file:
        text_file.write(raw_html)

    if auto_open:
        import webbrowser
        url = 'file://' + str(fpath)
        webbrowser.open(url)


def save_multiple_formats(fig, html_path, scale=3, width=1200, height=700):
    png_data = PLOT_CONVERTER.transform(fig, format="png", scale=scale, width=width, height=height)
    Path(html_path).parent.mkdir(exist_ok=True, parents=True)
    png_path = Path(html_path).with_suffix('.png')
    with open(png_path, 'wb') as f:
        f.write(png_data)

    html_path = png_path.with_suffix('.html')
    save_plot_with_external_script_link(fig, html_path)

    return fig


def get_project_dir():
    return Path(__file__).resolve().parents[2]


def load_config_json(path_from_root):
    with open(get_project_dir() / path_from_root) as file:
        items = json.load(file)
    return items


def load_api_keys_from_json(fpath):
    with open(fpath) as f:
        keys = json.load(f)
    return keys['api_key'], keys['api_secret']


def convert_timestamp_to_datetime(t):
    return datetime.datetime.fromtimestamp(int(t) / 1000)


def cast_all_to_float(df: pd.DataFrame, except_columns: List = None):
    if except_columns is None:
        except_columns = []
    for c in set(df.columns) - set(except_columns):
        try:
            df[c] = df[c].astype(float)
            df[c] = df[c].round(10)
        except ValueError:
            pass
