import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.data import load_zomato
from utils.charts import kpi_row, choropleth, scatter_map, bar_chart, histogram, pie_chart, box_plot, heatmap, scatter


def render():
    st.title("🍽️ Zomato Restaurant Analysis")
    st.caption("Dataset: Zomato India — 55,569 restaurants · Cities, cuisines, ratings, costs")

    with st.spinner("Loading dataset..."):
        df = load_zomato()

    if df.empty:
        st.error("Could not load Zomato dataset.")
        return

    # ── Sidebar filters ───────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### Filters")
        cities = sorted(df["city"].dropna().unique()) if "city" in df.columns else []
        sel_cities = st.multiselect("City", cities, key="zom_city")
        price_ranges = sorted(df["price_range"].dropna().unique()) if "price_range" in df.columns else []
        sel_price = st.multiselect("Price Range (1=cheap, 4=expensive)", price_ranges, key="zom_price")
        if "aggregate_rating" in df.columns:
            min_rating = st.slider("Min Rating", 0.0, 5.0, 3.0, 0.1, key="zom_rating")

    fdf = df.copy()
    if sel_cities:
        fdf = fdf[fdf["city"].isin(sel_cities)]
    if sel_price:
        fdf = fdf[fdf["price_range"].isin(sel_price)]
    if "aggregate_rating" in fdf.columns:
        fdf = fdf[fdf["aggregate_rating"] >= min_rating]

    # ── KPIs ──────────────────────────────────────────────────────────────────
    avg_rating = fdf["aggregate_rating"].mean() if "aggregate_rating" in fdf.columns else 0
    avg_cost = fdf["average_cost_for_two"].mean() if "average_cost_for_two" in fdf.columns else 0
    total_votes = fdf["votes"].sum() if "votes" in fdf.columns else 0

    kpi_row(st, [
        {"label": "Total Restaurants", "value": f"{len(fdf):,}"},
        {"label": "Cities", "value": str(fdf["city"].nunique()) if "city" in fdf.columns else "—"},
        {"label": "Avg Rating", "value": f"{avg_rating:.2f} ⭐"},
        {"label": "Avg Cost for 2", "value": f"₹{avg_cost:,.0f}"},
        {"label": "Total Votes", "value": f"{total_votes/1e6:.1f}M"},
        {"label": "Cuisines", "value": str(fdf["cuisines"].nunique()) if "cuisines" in fdf.columns else "—"},
    ])
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["🏙️ Cities", "⭐ Ratings", "🍜 Cuisines", "🔬 Analysis"])

    # ── Tab 1: Cities ─────────────────────────────────────────────────────────
    with tab1:
        city_stats = fdf.groupby("city").agg(
            Restaurants=("name", "count"),
            Avg_Rating=("aggregate_rating", "mean"),
            Avg_Cost=("average_cost_for_two", "mean"),
            Total_Votes=("votes", "sum"),
        ).reset_index()
        city_stats["Avg_Rating"] = city_stats["Avg_Rating"].round(2)
        city_stats["Avg_Cost"] = city_stats["Avg_Cost"].round(0)

        col1, col2 = st.columns(2)
        with col1:
            top_cities = city_stats.nlargest(20, "Restaurants")
            fig = px.bar(top_cities, x="Restaurants", y="city", orientation="h",
                         color="Avg_Rating", color_continuous_scale="RdYlGn",
                         title="Top 20 Cities — Restaurant Count",
                         color_continuous_midpoint=3.5)
            fig.update_layout(height=550, yaxis=dict(autorange="reversed"),
                              template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            top_rated_cities = city_stats[city_stats["Restaurants"] >= 50].nlargest(20, "Avg_Rating")
            fig = px.bar(top_rated_cities, x="Avg_Rating", y="city", orientation="h",
                         color="Avg_Rating", color_continuous_scale="Greens",
                         title="Top Rated Cities (min 50 restaurants)")
            fig.update_layout(height=550, yaxis=dict(autorange="reversed"),
                              template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

        # Scatter map
        if "latitude" in fdf.columns and "longitude" in fdf.columns:
            map_df = fdf.dropna(subset=["latitude","longitude"]).sample(min(5000, len(fdf)))
            fig = px.scatter_mapbox(
                map_df, lat="latitude", lon="longitude",
                color="aggregate_rating", size="votes",
                hover_name="name", hover_data=["city","cuisines","average_cost_for_two"],
                color_continuous_scale="RdYlGn",
                zoom=4, height=500,
                title="Restaurant Locations (sample 5K)",
                mapbox_style="carto-positron",
            )
            fig.update_layout(margin=dict(l=0,r=0,t=40,b=0))
            st.plotly_chart(fig, use_container_width=True)

    # ── Tab 2: Ratings ────────────────────────────────────────────────────────
    with tab2:
        col1, col2 = st.columns(2)

        with col1:
            if "rating_text" in fdf.columns:
                rt = fdf["rating_text"].value_counts().reset_index()
                rt.columns = ["Rating Text", "Count"]
                st.plotly_chart(
                    pie_chart(rt, "Rating Text", "Count", "Rating Text Distribution"),
                    use_container_width=True
                )

        with col2:
            fig = px.histogram(fdf, x="aggregate_rating", nbins=25,
                               title="Rating Distribution",
                               color_discrete_sequence=["#0066cc"],
                               template="plotly_white")
            fig.update_layout(height=380)
            st.plotly_chart(fig, use_container_width=True)

        # Rating vs Cost scatter
        fig = px.scatter(
            fdf.dropna(subset=["aggregate_rating","average_cost_for_two"]).sample(min(5000,len(fdf))),
            x="average_cost_for_two", y="aggregate_rating",
            color="price_range" if "price_range" in fdf.columns else None,
            hover_name="name", trendline="ols",
            title="Cost for Two vs Rating",
            labels={"average_cost_for_two":"Avg Cost for 2 (₹)", "aggregate_rating":"Rating"},
            template="plotly_white", opacity=0.5,
        )
        fig.update_layout(height=430)
        st.plotly_chart(fig, use_container_width=True)

        # Rating by price range
        if "price_range" in fdf.columns:
            pr_map = {1: "Budget", 2: "Moderate", 3: "Expensive", 4: "Luxury"}
            fdf["Price Category"] = fdf["price_range"].map(pr_map)
            st.plotly_chart(
                box_plot(fdf.dropna(subset=["Price Category"]),
                         "Price Category", "aggregate_rating",
                         title="Rating Distribution by Price Category"),
                use_container_width=True
            )

    # ── Tab 3: Cuisines ───────────────────────────────────────────────────────
    with tab3:
        # Explode cuisines (comma-separated)
        if "cuisines" in fdf.columns:
            cuis_exploded = fdf.assign(
                cuisine=fdf["cuisines"].str.split(",")
            ).explode("cuisine")
            cuis_exploded["cuisine"] = cuis_exploded["cuisine"].str.strip()

            col1, col2 = st.columns(2)
            with col1:
                top_cuis = cuis_exploded["cuisine"].value_counts().head(20).reset_index()
                top_cuis.columns = ["Cuisine", "Count"]
                fig = px.bar(top_cuis, x="Count", y="Cuisine", orientation="h",
                             color="Count", color_continuous_scale="Oranges",
                             title="Top 20 Most Common Cuisines")
                fig.update_layout(height=550, yaxis=dict(autorange="reversed"),
                                  template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                cuis_rating = cuis_exploded.groupby("cuisine").agg(
                    Restaurants=("name","count"),
                    Avg_Rating=("aggregate_rating","mean"),
                ).reset_index()
                top_rated_cuis = cuis_rating[cuis_rating["Restaurants"]>=50].nlargest(20,"Avg_Rating")
                top_rated_cuis["Avg_Rating"] = top_rated_cuis["Avg_Rating"].round(2)
                fig = px.bar(top_rated_cuis, x="Avg_Rating", y="cuisine", orientation="h",
                             color="Avg_Rating", color_continuous_scale="Greens",
                             title="Top Rated Cuisines (min 50 restaurants)")
                fig.update_layout(height=550, yaxis=dict(autorange="reversed"),
                                  template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)

        # Delivery vs Takeaway
        col1, col2 = st.columns(2)
        if "delivery" in fdf.columns:
            dlv = fdf["delivery"].value_counts().reset_index()
            dlv.columns = ["Delivery","Count"]
            with col1:
                st.plotly_chart(pie_chart(dlv, "Delivery", "Count", "Delivery Available"),
                                use_container_width=True)
        if "takeaway" in fdf.columns:
            tak = fdf["takeaway"].value_counts().reset_index()
            tak.columns = ["Takeaway","Count"]
            with col2:
                st.plotly_chart(pie_chart(tak, "Takeaway", "Count", "Takeaway Available"),
                                use_container_width=True)

    # ── Tab 4: Analysis ───────────────────────────────────────────────────────
    with tab4:
        # Establishment type
        if "establishment" in fdf.columns:
            est = fdf["establishment"].value_counts().head(15).reset_index()
            est.columns = ["Establishment","Count"]
            fig = px.bar(est, x="Count", y="Establishment", orientation="h",
                         color="Count", color_continuous_scale="Blues",
                         title="Restaurant Establishment Types")
            fig.update_layout(height=480, yaxis=dict(autorange="reversed"),
                              template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

        # Correlation matrix
        num_cols = [c for c in ["aggregate_rating","average_cost_for_two","votes",
                                "price_range","No. of Cuisines"] if c in fdf.columns]
        if len(num_cols) >= 2:
            corr = fdf[num_cols].corr()
            st.plotly_chart(heatmap(corr, "Correlation Matrix"), use_container_width=True)

        # Top restaurants by votes
        st.subheader("Most Voted Restaurants")
        top_rest = fdf.nlargest(15, "votes")[
            ["name","city","cuisines","aggregate_rating","average_cost_for_two","votes"]
        ].reset_index(drop=True)
        top_rest.columns = ["Name","City","Cuisines","Rating","Avg Cost (₹)","Votes"]
        st.dataframe(top_rest, use_container_width=True, hide_index=True)

        # Quick insights
        st.subheader("Quick Insights")
        top_city = fdf["city"].value_counts().index[0] if "city" in fdf.columns else "—"
        st.markdown(f"- **Most restaurants in:** {top_city}")
        if "cuisines" in fdf.columns:
            top_cuisine = fdf["cuisines"].str.split(",").explode().str.strip().value_counts().index[0]
            st.markdown(f"- **Most popular cuisine:** {top_cuisine}")
        if "rating_text" in fdf.columns:
            top_rt = fdf["rating_text"].value_counts().index[0]
            st.markdown(f"- **Most common rating:** {top_rt}")
        if "delivery" in fdf.columns:
            dlv_pct = (fdf["delivery"] == "Yes").mean() * 100
            st.markdown(f"- **Restaurants with delivery:** {dlv_pct:.1f}%")
        if "aggregate_rating" in fdf.columns:
            pct_good = (fdf["aggregate_rating"] >= 4.0).mean() * 100
            st.markdown(f"- **Restaurants rated ≥4.0:** {pct_good:.1f}%")
