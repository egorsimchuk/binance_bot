import plotly.graph_objects as go

from src.constants import time_col


def plot_asset_history(plot_df, title, width=None, height=None):
    fig = go.Figure()
    x = plot_df[time_col]
    fig.add_trace(
        go.Scatter(
            x=x,
            y=plot_df["usdt_cash_in_cum"],
            mode="lines",
            line_color="blue",
            line_width=1,
            name="cash in",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=plot_df["coin_cum_usdt_value"],
            fill="tozeroy",
            mode="lines",
            line_color="green",
            line_width=0.5,
            name="assets value",
        )
    )
    fig.update_layout(yaxis_title="usd", title=title, width=width, height=height)
    return fig
