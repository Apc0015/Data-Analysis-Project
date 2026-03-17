import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.data import load_crypto_prices, load_crypto_history, load_crypto_market_chart
from utils.charts import kpi_row, candlestick, price_volume_chart, bar_chart, heatmap, scatter

COINS = {
    "Bitcoin": "bitcoin",
    "Ethereum": "ethereum",
    "Dogecoin": "dogecoin",
    "Solana": "solana",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "Cardano": "cardano",
}


def render():
    st.title("₿ Cryptocurrency Dashboard")
    st.caption("Live data from [CoinGecko](https://www.coingecko.com) — prices refresh every 60 seconds")

    # ── Live price table ─────────────────────────────────────────────────────
    coin_ids = ",".join(COINS.values())
    with st.spinner("Fetching live prices..."):
        prices_df = load_crypto_prices(coin_ids)

    if prices_df.empty:
        st.error("Could not load live price data. CoinGecko may be rate-limiting — try again shortly.")
    else:
        # KPI row for top 4 coins
        top4 = prices_df.head(4)
        metrics = []
        for _, row in top4.iterrows():
            chg = row.get("price_change_percentage_24h", 0) or 0
            metrics.append({
                "label": row.get("name", ""),
                "value": f"${row.get('current_price', 0):,.2f}",
                "delta": f"{chg:+.2f}% (24h)",
                "delta_color": "normal",
            })
        kpi_row(st, metrics)
        st.markdown("---")

        # Full market table
        with st.expander("📊 Live Market Overview", expanded=True):
            display_cols = {
                "name": "Coin",
                "current_price": "Price (USD)",
                "market_cap": "Market Cap",
                "total_volume": "24h Volume",
                "price_change_percentage_24h": "24h %",
                "price_change_percentage_7d_in_currency": "7d %",
                "price_change_percentage_30d_in_currency": "30d %",
                "circulating_supply": "Circulating Supply",
                "ath": "ATH",
                "ath_change_percentage": "ATH %",
            }
            avail = {k: v for k, v in display_cols.items() if k in prices_df.columns}
            tbl = prices_df[list(avail.keys())].rename(columns=avail).copy()

            # Format
            for c in ["Price (USD)", "ATH"]:
                if c in tbl:
                    tbl[c] = tbl[c].apply(lambda x: f"${x:,.4f}" if x < 1 else f"${x:,.2f}")
            for c in ["Market Cap", "24h Volume"]:
                if c in tbl:
                    tbl[c] = tbl[c].apply(lambda x: f"${x/1e9:.2f}B" if x >= 1e9 else f"${x/1e6:.1f}M")
            for c in ["24h %", "7d %", "30d %", "ATH %"]:
                if c in tbl:
                    tbl[c] = tbl[c].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "N/A")

            st.dataframe(tbl, use_container_width=True, hide_index=True)

        # Market cap bar chart
        if "market_cap" in prices_df.columns:
            mc = prices_df[["name", "market_cap"]].copy()
            mc["Market Cap ($B)"] = mc["market_cap"] / 1e9
            st.plotly_chart(
                bar_chart(mc, "Market Cap ($B)", "name", title="Market Cap Comparison ($B)", orientation="h"),
                use_container_width=True
            )

    st.markdown("---")

    # ── Deep dive per coin ───────────────────────────────────────────────────
    st.subheader("Deep Dive — Historical Analysis")
    col1, col2, col3 = st.columns(3)
    with col1:
        coin_name = st.selectbox("Coin", list(COINS.keys()))
    with col2:
        days = st.selectbox("Period", [7, 14, 30, 90, 180, 365], index=3)
    with col3:
        chart_type = st.selectbox("Chart type", ["Candlestick", "Line + Volume"])

    coin_id = COINS[coin_name]

    col_a, col_b = st.columns([2, 1])
    with col_a:
        if chart_type == "Candlestick":
            with st.spinner("Loading OHLC data..."):
                ohlc = load_crypto_history(coin_id, days)
            if not ohlc.empty:
                st.plotly_chart(
                    candlestick(ohlc, title=f"{coin_name} — {days}d OHLC"),
                    use_container_width=True
                )
            else:
                st.info("OHLC data unavailable for this period.")
        else:
            with st.spinner("Loading market chart..."):
                mc_df = load_crypto_market_chart(coin_id, days)
            if not mc_df.empty:
                st.plotly_chart(
                    price_volume_chart(mc_df, title=f"{coin_name} — Price & Volume ({days}d)"),
                    use_container_width=True
                )
            else:
                st.info("Market chart data unavailable.")

    with col_b:
        # Stats from market chart
        with st.spinner(""):
            mc_df2 = load_crypto_market_chart(coin_id, days)
        if not mc_df2.empty:
            p = mc_df2["Price"]
            st.metric("Current Price", f"${p.iloc[-1]:,.4f}" if p.iloc[-1] < 1 else f"${p.iloc[-1]:,.2f}")
            st.metric("Period High", f"${p.max():,.2f}")
            st.metric("Period Low", f"${p.min():,.2f}")
            change_pct = (p.iloc[-1] - p.iloc[0]) / p.iloc[0] * 100
            st.metric("Period Change", f"{change_pct:+.2f}%", delta_color="normal")
            volatility = p.pct_change().std() * 100
            st.metric("Daily Volatility", f"{volatility:.2f}%")

    # ── Multi-coin comparison ─────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Multi-Coin Performance Comparison")
    selected_coins = st.multiselect("Select coins to compare", list(COINS.keys()),
                                    default=["Bitcoin", "Ethereum", "Solana"])
    comp_days = st.slider("Comparison period (days)", 7, 365, 30)

    if selected_coins:
        all_dfs = []
        for cn in selected_coins:
            with st.spinner(f"Loading {cn}..."):
                d = load_crypto_market_chart(COINS[cn], comp_days)
            if not d.empty:
                d = d[["Date", "Price"]].copy()
                d["Coin"] = cn
                # Normalize to 100 at start
                d["Normalized"] = d["Price"] / d["Price"].iloc[0] * 100
                all_dfs.append(d)

        if all_dfs:
            comp_df = pd.concat(all_dfs, ignore_index=True)
            fig = px.line(
                comp_df, x="Date", y="Normalized", color="Coin",
                title=f"Normalized Performance (base=100, {comp_days}d)",
                template="plotly_white",
            )
            fig.update_layout(hovermode="x unified", height=420)
            st.plotly_chart(fig, use_container_width=True)
