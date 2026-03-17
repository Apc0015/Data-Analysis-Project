import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.data import load_terrorism
from utils.charts import kpi_row, choropleth, scatter_map, bar_chart, line_chart, heatmap, pie_chart


def render():
    st.title("💣 Global Terrorism Dashboard")
    st.caption("Dataset: Global Terrorism Database (GTD) — 1970 to 2017 · 181,691 incidents")

    with st.spinner("Loading dataset..."):
        df = load_terrorism()

    if df.empty:
        st.warning(
            "**Global Terrorism dataset not available on this deployment.**\n\n"
            "The GTD CSV is 155 MB and cannot be stored in the GitHub repo. "
            "To enable this dashboard locally:\n"
            "1. Download from [Kaggle — Global Terrorism Database](https://www.kaggle.com/datasets/START-UMD/gtd)\n"
            "2. Place the file at `projects/terrorism/data/globalterrorismdb_utf8.csv`\n"
            "3. Run `streamlit run streamlit_app/app.py`"
        )
        return

    # ── Sidebar filters ───────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### Filters")
        year_range = st.slider("Year range", int(df["Year"].min()), int(df["Year"].max()),
                               (2000, 2017), key="terr_year")
        regions = st.multiselect("Region", sorted(df["Region"].dropna().unique()),
                                 key="terr_region")
        attack_types = st.multiselect("Attack type", sorted(df["Attack Type"].dropna().unique()),
                                      key="terr_attack")

    fdf = df[(df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1])]
    if regions:
        fdf = fdf[fdf["Region"].isin(regions)]
    if attack_types:
        fdf = fdf[fdf["Attack Type"].isin(attack_types)]

    # ── KPIs ──────────────────────────────────────────────────────────────────
    kpi_row(st, [
        {"label": "Total Incidents", "value": f"{len(fdf):,}"},
        {"label": "Total Killed", "value": f"{int(fdf['Killed'].sum()):,}"},
        {"label": "Total Wounded", "value": f"{int(fdf['Wounded'].sum()):,}"},
        {"label": "Countries Affected", "value": str(fdf["Country"].nunique())},
        {"label": "Terrorist Groups", "value": str(fdf["Group"].nunique())},
        {"label": "Success Rate", "value": f"{fdf['Success'].mean()*100:.1f}%"},
    ])
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ World Map", "📈 Trends", "🏆 Rankings", "🔬 Deep Dive"])

    # ── Tab 1: Map ────────────────────────────────────────────────────────────
    with tab1:
        col1, col2 = st.columns([3, 1])
        with col2:
            map_metric = st.selectbox("Color by", ["Incidents", "Killed", "Wounded", "Casualties"])
        country_stats = fdf.groupby("Country").agg(
            Incidents=("Year", "count"),
            Killed=("Killed", "sum"),
            Wounded=("Wounded", "sum"),
            Casualties=("Casualties", "sum"),
        ).reset_index()
        with col1:
            st.plotly_chart(
                choropleth(country_stats, "Country", map_metric,
                           f"Terrorism — {map_metric} by Country", color_scale="YlOrRd"),
                use_container_width=True
            )

        # Bubble map
        city_stats = fdf.dropna(subset=["Lat", "Lon"]).groupby(["City", "Lat", "Lon"]).agg(
            Incidents=("Year", "count"),
            Killed=("Killed", "sum"),
        ).reset_index()
        st.plotly_chart(
            scatter_map(city_stats, "Lat", "Lon", "Killed", "Incidents",
                        "City", "Attack Locations (bubble = incident count)", "YlOrRd"),
            use_container_width=True
        )

    # ── Tab 2: Trends ─────────────────────────────────────────────────────────
    with tab2:
        yearly = fdf.groupby("Year").agg(
            Incidents=("Year", "count"),
            Killed=("Killed", "sum"),
            Wounded=("Wounded", "sum"),
        ).reset_index()

        st.plotly_chart(
            line_chart(yearly, "Year", "Incidents", title="Annual Terrorism Incidents"),
            use_container_width=True
        )

        melted = yearly.melt("Year", ["Killed", "Wounded"], var_name="Type", value_name="Count")
        st.plotly_chart(
            line_chart(melted, "Year", "Count", color="Type",
                       title="Annual Casualties (Killed vs Wounded)"),
            use_container_width=True
        )

        # Region trend
        region_year = fdf.groupby(["Year", "Region"]).size().reset_index(name="Incidents")
        fig = px.area(region_year, x="Year", y="Incidents", color="Region",
                      title="Incidents by Region Over Time", template="plotly_white")
        fig.update_layout(height=400, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    # ── Tab 3: Rankings ───────────────────────────────────────────────────────
    with tab3:
        col1, col2 = st.columns(2)

        with col1:
            top_countries = country_stats.nlargest(15, "Incidents")[["Country", "Incidents", "Killed"]]
            st.plotly_chart(
                bar_chart(top_countries, "Incidents", "Country",
                          title="Top 15 Countries by Incidents", orientation="h"),
                use_container_width=True
            )

        with col2:
            top_groups = fdf[fdf["Group"] != "Unknown"].groupby("Group").agg(
                Incidents=("Year", "count"),
                Killed=("Killed", "sum"),
            ).nlargest(15, "Incidents").reset_index()
            st.plotly_chart(
                bar_chart(top_groups, "Incidents", "Group",
                          title="Top 15 Most Active Groups", orientation="h"),
                use_container_width=True
            )

        col3, col4 = st.columns(2)
        with col3:
            attack_counts = fdf["Attack Type"].value_counts().reset_index()
            attack_counts.columns = ["Attack Type", "Count"]
            st.plotly_chart(
                pie_chart(attack_counts, "Attack Type", "Count", "Attack Types"),
                use_container_width=True
            )
        with col4:
            target_counts = fdf["Target Type"].value_counts().reset_index()
            target_counts.columns = ["Target Type", "Count"]
            st.plotly_chart(
                pie_chart(target_counts, "Target Type", "Count", "Target Types"),
                use_container_width=True
            )

    # ── Tab 4: Deep Dive ─────────────────────────────────────────────────────
    with tab4:
        st.subheader("Region vs Attack Type Heatmap")
        pivot = fdf.groupby(["Region", "Attack Type"]).size().unstack(fill_value=0)
        fig = px.imshow(pivot, title="Incidents: Region × Attack Type",
                        template="plotly_white", color_continuous_scale="YlOrRd",
                        text_auto=True, aspect="auto")
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Deadliest Incidents")
        worst = fdf.nlargest(20, "Killed")[
            ["Year", "Country", "City", "Attack Type", "Group", "Killed", "Wounded"]
        ].reset_index(drop=True)
        st.dataframe(worst, use_container_width=True)

        # Quick insights
        st.subheader("Quick Insights")
        most_active = fdf[fdf["Group"] != "Unknown"]["Group"].value_counts().index[0]
        deadliest_country = country_stats.nlargest(1, "Killed")["Country"].values[0]
        peak_year = yearly.nlargest(1, "Incidents")["Year"].values[0]
        st.markdown(f"- **Most active group:** {most_active}")
        st.markdown(f"- **Most deaths in:** {deadliest_country}")
        st.markdown(f"- **Peak year for attacks:** {peak_year}")
        st.markdown(f"- **Most common attack:** {fdf['Attack Type'].mode()[0]}")
        st.markdown(f"- **Most targeted:** {fdf['Target Type'].mode()[0]}")
