import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

PALETTE = px.colors.qualitative.Bold
TEMPLATE = "plotly_white"


def kpi_row(st, metrics: list[dict]):
    """Render a row of KPI metric cards.
    metrics = [{"label": ..., "value": ..., "delta": ..., "delta_color": "normal"}, ...]
    """
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        col.metric(
            label=m["label"],
            value=m["value"],
            delta=m.get("delta"),
            delta_color=m.get("delta_color", "normal"),
        )


def choropleth(df, locations_col, color_col, title, hover_data=None, color_scale="Reds"):
    fig = px.choropleth(
        df,
        locations=locations_col,
        locationmode="country names",
        color=color_col,
        hover_name=locations_col,
        hover_data=hover_data,
        color_continuous_scale=color_scale,
        title=title,
        template=TEMPLATE,
    )
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=420)
    return fig


def scatter_map(df, lat_col, lon_col, color_col, size_col, hover_name, title, color_scale="Reds"):
    fig = px.scatter_geo(
        df.dropna(subset=[lat_col, lon_col]),
        lat=lat_col,
        lon=lon_col,
        color=color_col,
        size=size_col,
        hover_name=hover_name,
        color_continuous_scale=color_scale,
        title=title,
        template=TEMPLATE,
        projection="natural earth",
    )
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=450)
    return fig


def line_chart(df, x, y, color=None, title="", labels=None):
    fig = px.line(
        df, x=x, y=y, color=color,
        title=title, labels=labels or {},
        template=TEMPLATE, color_discrete_sequence=PALETTE,
    )
    fig.update_layout(hovermode="x unified", height=380)
    return fig


def bar_chart(df, x, y, color=None, title="", orientation="v", top_n=None):
    if top_n:
        df = df.nlargest(top_n, y) if orientation == "v" else df.nlargest(top_n, x)
    fig = px.bar(
        df, x=x, y=y, color=color,
        title=title, orientation=orientation,
        template=TEMPLATE, color_discrete_sequence=PALETTE,
    )
    fig.update_layout(height=380)
    return fig


def candlestick(df, title=""):
    fig = go.Figure(data=[go.Candlestick(
        x=df["Date"],
        open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing_line_color="#00c896",
        decreasing_line_color="#ff4b4b",
    )])
    fig.update_layout(
        title=title, template=TEMPLATE,
        xaxis_rangeslider_visible=False, height=420,
    )
    return fig


def area_chart(df, x, y, title="", color=None):
    fig = px.area(
        df, x=x, y=y, color=color,
        title=title, template=TEMPLATE,
        color_discrete_sequence=PALETTE,
    )
    fig.update_layout(hovermode="x unified", height=380)
    return fig


def heatmap(corr_df, title="Correlation Matrix"):
    fig = px.imshow(
        corr_df,
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1,
        title=title,
        template=TEMPLATE,
        text_auto=".2f",
        aspect="auto",
    )
    fig.update_layout(height=420)
    return fig


def pie_chart(df, names, values, title=""):
    fig = px.pie(
        df, names=names, values=values,
        title=title, template=TEMPLATE,
        color_discrete_sequence=PALETTE,
        hole=0.4,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(height=380, showlegend=True)
    return fig


def histogram(df, x, nbins=40, color=None, title=""):
    fig = px.histogram(
        df, x=x, nbins=nbins, color=color,
        title=title, template=TEMPLATE,
        color_discrete_sequence=PALETTE,
    )
    fig.update_layout(height=350)
    return fig


def box_plot(df, x, y, color=None, title=""):
    fig = px.box(
        df, x=x, y=y, color=color,
        title=title, template=TEMPLATE,
        color_discrete_sequence=PALETTE,
    )
    fig.update_layout(height=380)
    return fig


def scatter(df, x, y, color=None, size=None, hover_name=None, trendline=None, title=""):
    fig = px.scatter(
        df, x=x, y=y, color=color, size=size,
        hover_name=hover_name, trendline=trendline,
        title=title, template=TEMPLATE,
        color_discrete_sequence=PALETTE,
    )
    fig.update_layout(height=400)
    return fig


def price_volume_chart(df, title=""):
    """Dual-axis price + volume chart."""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.7, 0.3], vertical_spacing=0.04)
    fig.add_trace(go.Scatter(x=df["Date"], y=df["Price"], name="Price",
                             line=dict(color="#00c896")), row=1, col=1)
    fig.add_trace(go.Bar(x=df["Date"], y=df["Volume"], name="Volume",
                         marker_color="#4c78a8", opacity=0.6), row=2, col=1)
    fig.update_layout(title=title, template=TEMPLATE,
                      hovermode="x unified", height=480, showlegend=True)
    return fig
