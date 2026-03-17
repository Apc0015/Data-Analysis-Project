import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.data import load_covid_world, load_covid_global, load_covid_historical
from utils.charts import kpi_row, choropleth, scatter_map, line_chart, bar_chart, heatmap, pie_chart


def render():
    st.title("🦠 COVID-19 Global Dashboard")
    st.caption("Live data from [disease.sh](https://disease.sh) — refreshes every 5 minutes")

    # ── Global KPIs ──────────────────────────────────────────────────────────
    global_stats = load_covid_global()
    if global_stats:
        def fmt(n):
            if n >= 1_000_000:
                return f"{n/1_000_000:.2f}M"
            if n >= 1_000:
                return f"{n/1_000:.1f}K"
            return str(n)

        kpi_row(st, [
            {"label": "Total Cases", "value": fmt(global_stats.get("cases", 0)),
             "delta": f"+{fmt(global_stats.get('todayCases', 0))} today", "delta_color": "inverse"},
            {"label": "Total Deaths", "value": fmt(global_stats.get("deaths", 0)),
             "delta": f"+{fmt(global_stats.get('todayDeaths', 0))} today", "delta_color": "inverse"},
            {"label": "Recovered", "value": fmt(global_stats.get("recovered", 0))},
            {"label": "Active Cases", "value": fmt(global_stats.get("active", 0))},
            {"label": "Critical", "value": fmt(global_stats.get("critical", 0)), "delta_color": "inverse"},
            {"label": "Countries", "value": str(global_stats.get("affectedCountries", 0))},
        ])
    st.markdown("---")

    # ── Load country data ────────────────────────────────────────────────────
    with st.spinner("Loading country data..."):
        df = load_covid_world()

    if df.empty:
        st.error("Could not load live data. Please check your internet connection.")
        return

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ World Map", "📈 Trends", "🏆 Country Rankings", "🔬 Analysis"])

    # ── Tab 1: World Map ─────────────────────────────────────────────────────
    with tab1:
        col1, col2 = st.columns([3, 1])
        with col2:
            map_metric = st.selectbox("Color by", ["Total Cases", "Total Deaths", "Active",
                                                    "Cases/1M", "Deaths/1M", "Mortality Rate (%)"])
            color_scale = st.selectbox("Color scale", ["Reds", "Blues", "YlOrRd", "Viridis", "Plasma"])
        with col1:
            fig = choropleth(df, "Country", map_metric,
                             f"COVID-19 — {map_metric} by Country",
                             hover_data=["Total Cases", "Total Deaths", "Recovered", "Population"],
                             color_scale=color_scale)
            st.plotly_chart(fig, use_container_width=True)

        st.plotly_chart(
            scatter_map(df, "Lat", "Lon", "Total Cases", "Total Cases",
                        "Country", "Bubble Map — Total Cases", "Reds"),
            use_container_width=True
        )

    # ── Tab 2: Trends ────────────────────────────────────────────────────────
    with tab2:
        col1, col2 = st.columns([2, 1])
        with col2:
            country = st.selectbox("Country", ["all"] + sorted(df["Country"].dropna().tolist()),
                                   key="trend_country")
            days = st.slider("Days", 30, 365, 90, key="trend_days")
        with col1:
            with st.spinner("Loading historical data..."):
                hist = load_covid_historical(country, days)
            if not hist.empty:
                st.plotly_chart(
                    line_chart(hist.melt("Date", ["Cases", "Deaths", "Recovered"],
                                         var_name="Metric", value_name="Count"),
                               "Date", "Count", color="Metric",
                               title=f"Cumulative Trend — {country}"),
                    use_container_width=True
                )
                st.plotly_chart(
                    line_chart(hist.melt("Date", ["Daily Cases", "Daily Deaths"],
                                         var_name="Metric", value_name="Count"),
                               "Date", "Count", color="Metric",
                               title=f"Daily New Cases & Deaths — {country}"),
                    use_container_width=True
                )
            else:
                st.info("No historical data available for this selection.")

    # ── Tab 3: Country Rankings ───────────────────────────────────────────────
    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            rank_metric = st.selectbox("Rank by", ["Total Cases", "Total Deaths", "Active",
                                                   "Cases/1M", "Deaths/1M", "Mortality Rate (%)"])
            top_n = st.slider("Top N countries", 10, 30, 15)
        top_df = df.nlargest(top_n, rank_metric)[["Country", rank_metric]].dropna()
        st.plotly_chart(
            bar_chart(top_df, rank_metric, "Country", title=f"Top {top_n} — {rank_metric}",
                      orientation="h"),
            use_container_width=True
        )

        # Continent breakdown
        cont = df.groupby("Continent")[["Total Cases", "Total Deaths", "Recovered"]].sum().reset_index()
        cont = cont[cont["Continent"].notna() & (cont["Continent"] != "")]
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(
                pie_chart(cont, "Continent", "Total Cases", "Cases by Continent"),
                use_container_width=True
            )
        with col2:
            st.plotly_chart(
                pie_chart(cont, "Continent", "Total Deaths", "Deaths by Continent"),
                use_container_width=True
            )

    # ── Tab 4: Analysis ───────────────────────────────────────────────────────
    with tab4:
        numeric_cols = ["Total Cases", "Total Deaths", "Recovered", "Active",
                        "Cases/1M", "Deaths/1M", "Tests/1M", "Mortality Rate (%)", "Recovery Rate (%)"]
        available = [c for c in numeric_cols if c in df.columns]
        corr = df[available].corr()
        st.plotly_chart(heatmap(corr, "Correlation Matrix"), use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            x_col = st.selectbox("X axis", available, index=available.index("Cases/1M") if "Cases/1M" in available else 0)
        with col2:
            y_col = st.selectbox("Y axis", available, index=available.index("Deaths/1M") if "Deaths/1M" in available else 1)

        import plotly.express as px
        fig = px.scatter(
            df.dropna(subset=[x_col, y_col]),
            x=x_col, y=y_col, color="Continent",
            hover_name="Country", trendline="ols",
            title=f"{x_col} vs {y_col}",
            template="plotly_white",
        )
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

        # Quick insights
        st.subheader("Quick Insights")
        top3_cases = df.nlargest(3, "Total Cases")["Country"].tolist()
        top3_mortality = df[df["Total Cases"] > 10000].nlargest(3, "Mortality Rate (%)")
        st.markdown(f"- **Most cases:** {', '.join(top3_cases)}")
        st.markdown(f"- **Highest mortality rate (>10K cases):** " +
                    ", ".join([f"{r['Country']} ({r['Mortality Rate (%)']:.1f}%)"
                               for _, r in top3_mortality.iterrows()]))
        avg_mortality = df[df["Total Cases"] > 10000]["Mortality Rate (%)"].mean()
        st.markdown(f"- **Average mortality rate (countries with >10K cases):** {avg_mortality:.2f}%")
