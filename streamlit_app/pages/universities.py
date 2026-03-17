import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.data import load_universities
from utils.charts import kpi_row, choropleth, bar_chart, scatter, heatmap, box_plot


def render():
    st.title("🎓 World University Rankings Dashboard")
    st.caption("Dataset: CWUR Rankings — 2012 to 2015 · 2,200 universities · 59 countries")

    with st.spinner("Loading dataset..."):
        df = load_universities()

    if df.empty:
        st.error("Could not load universities dataset.")
        return

    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]

    # ── Sidebar filters ───────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### Filters")
        years = sorted(df["year"].dropna().unique().astype(int).tolist()) if "year" in df.columns else []
        sel_year = st.selectbox("Year", years, index=len(years)-1 if years else 0, key="uni_year")
        countries = sorted(df["country"].dropna().unique()) if "country" in df.columns else []
        sel_countries = st.multiselect("Country", countries, key="uni_country")

    fdf = df[df["year"] == sel_year] if "year" in df.columns else df
    if sel_countries:
        fdf = fdf[fdf["country"].isin(sel_countries)]

    # ── KPIs ──────────────────────────────────────────────────────────────────
    kpi_row(st, [
        {"label": "Universities", "value": f"{len(fdf):,}"},
        {"label": "Countries", "value": str(fdf["country"].nunique()) if "country" in fdf.columns else "—"},
        {"label": "#1 University", "value": fdf.nsmallest(1, "world_rank")["institution"].values[0]
         if "world_rank" in fdf.columns and len(fdf) > 0 else "—"},
        {"label": "Avg Score", "value": f"{fdf['score'].mean():.2f}" if "score" in fdf.columns else "—"},
        {"label": "Max Score", "value": f"{fdf['score'].max():.2f}" if "score" in fdf.columns else "—"},
    ])
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ World Map", "🏆 Rankings", "📊 Metrics", "🔬 Analysis"])

    score_cols = [c for c in ["quality_of_education", "alumni_employment", "quality_of_faculty",
                               "publications", "influence", "citations",
                               "broad_impact", "patents", "score"] if c in fdf.columns]

    # ── Tab 1: Map ────────────────────────────────────────────────────────────
    with tab1:
        country_stats = fdf.groupby("country").agg(
            Universities=("institution", "count"),
            Avg_Score=("score", "mean"),
            Best_Rank=("world_rank", "min"),
        ).reset_index().rename(columns={"country": "Country"})
        country_stats["Avg_Score"] = country_stats["Avg_Score"].round(2)

        col1, col2 = st.columns([3, 1])
        with col2:
            map_metric = st.selectbox("Color by", ["Universities", "Avg_Score", "Best_Rank"])
        with col1:
            st.plotly_chart(
                choropleth(country_stats, "Country", map_metric,
                           f"World Universities — {map_metric}", color_scale="Blues"),
                use_container_width=True
            )

        st.plotly_chart(
            bar_chart(country_stats.nlargest(20, "Universities"),
                      "Universities", "Country",
                      title="Top 20 Countries by University Count", orientation="h"),
            use_container_width=True
        )

    # ── Tab 2: Rankings ───────────────────────────────────────────────────────
    with tab2:
        top_n = st.slider("Show top N universities", 10, 100, 25, key="uni_topn")
        rank_col = st.selectbox("Rank by", score_cols, index=score_cols.index("score") if "score" in score_cols else 0)

        if "world_rank" in fdf.columns:
            top_unis = fdf.nsmallest(top_n, "world_rank")[
                ["world_rank", "institution", "country"] + ([rank_col] if rank_col in fdf.columns else [])
            ].rename(columns={"world_rank": "Rank", "institution": "University", "country": "Country"})
            st.dataframe(top_unis, use_container_width=True, hide_index=True)

        # Country comparison
        country_avg = fdf.groupby("country")[score_cols].mean().reset_index()
        country_avg = country_avg.rename(columns={"country": "Country"})
        st.plotly_chart(
            bar_chart(country_avg.nlargest(20, "score") if "score" in country_avg.columns
                      else country_avg.head(20),
                      "score" if "score" in country_avg.columns else score_cols[0],
                      "Country",
                      title="Top 20 Countries — Average Score", orientation="h"),
            use_container_width=True
        )

    # ── Tab 3: Metrics ────────────────────────────────────────────────────────
    with tab3:
        if len(score_cols) >= 2:
            col1, col2 = st.columns(2)
            with col1:
                x_m = st.selectbox("X metric", score_cols, key="uni_x")
            with col2:
                y_m = st.selectbox("Y metric", score_cols,
                                   index=1 if len(score_cols) > 1 else 0, key="uni_y")

            fig = px.scatter(
                fdf.dropna(subset=[x_m, y_m]),
                x=x_m, y=y_m,
                color="country" if "country" in fdf.columns else None,
                hover_name="institution" if "institution" in fdf.columns else None,
                trendline="ols",
                title=f"{x_m} vs {y_m}",
                template="plotly_white",
            )
            fig.update_layout(height=450, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        # Box plots per country (top 10 countries)
        if "country" in fdf.columns and "score" in fdf.columns:
            top10_countries = fdf["country"].value_counts().head(10).index.tolist()
            box_df = fdf[fdf["country"].isin(top10_countries)]
            st.plotly_chart(
                box_plot(box_df, "country", "score", title="Score Distribution — Top 10 Countries"),
                use_container_width=True
            )

    # ── Tab 4: Analysis ───────────────────────────────────────────────────────
    with tab4:
        if len(score_cols) >= 2:
            corr = fdf[score_cols].corr()
            st.plotly_chart(heatmap(corr, "Metric Correlations"), use_container_width=True)

        # Radar chart for top universities
        if len(score_cols) >= 3 and "institution" in fdf.columns:
            st.subheader("Radar: Top 5 Universities")
            top5 = fdf.nsmallest(5, "world_rank") if "world_rank" in fdf.columns else fdf.head(5)
            radar_cols = [c for c in ["quality_of_education", "alumni_employment",
                                      "quality_of_faculty", "publications",
                                      "influence", "citations"] if c in fdf.columns]
            if radar_cols:
                import plotly.graph_objects as go
                fig = go.Figure()
                for _, row in top5.iterrows():
                    vals = [row[c] for c in radar_cols]
                    vals_norm = [1 - (v / fdf[c].max()) for v, c in zip(vals, radar_cols)]  # lower rank = better
                    fig.add_trace(go.Scatterpolar(
                        r=vals_norm + [vals_norm[0]],
                        theta=radar_cols + [radar_cols[0]],
                        fill="toself",
                        name=row.get("institution", "")[:30],
                    ))
                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                    template="plotly_white", height=450,
                    title="Normalized Rankings (1 = best)",
                )
                st.plotly_chart(fig, use_container_width=True)

        # Quick insights
        st.subheader("Quick Insights")
        if "country" in fdf.columns:
            top_country = fdf["country"].value_counts().index[0]
            top_count = fdf["country"].value_counts().iloc[0]
            st.markdown(f"- **Most represented country:** {top_country} ({top_count} universities)")
        if "institution" in fdf.columns and "world_rank" in fdf.columns:
            top_uni = fdf.nsmallest(1, "world_rank")[["institution", "country"]].values[0]
            st.markdown(f"- **#1 University ({sel_year}):** {top_uni[0]} ({top_uni[1]})")
        if "score" in fdf.columns:
            pct_above_70 = (fdf["score"] >= 70).sum()
            st.markdown(f"- **Universities scoring ≥ 70:** {pct_above_70}")
