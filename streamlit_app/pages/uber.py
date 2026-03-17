import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.data import load_uber
from utils.charts import kpi_row, bar_chart, histogram, pie_chart, scatter, box_plot

WEEKDAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTH_ORDER = ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]


def render():
    st.title("🚗 Uber Rides Analysis")
    st.caption("Dataset: Uber Business Trip Records — 1,156 trips · 2016")

    with st.spinner("Loading dataset..."):
        df = load_uber()

    if df.empty:
        st.error("Could not load Uber dataset.")
        return

    # ── Sidebar filters ───────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### Filters")
        if "CATEGORY*" in df.columns:
            cats = st.multiselect("Category", sorted(df["CATEGORY*"].dropna().unique()), key="uber_cat")
        if "PURPOSE*" in df.columns:
            purposes = st.multiselect("Purpose", sorted(df["PURPOSE*"].dropna().unique()), key="uber_purp")

    fdf = df.copy()
    if "CATEGORY*" in df.columns and cats:
        fdf = fdf[fdf["CATEGORY*"].isin(cats)]
    if "PURPOSE*" in df.columns and purposes:
        fdf = fdf[fdf["PURPOSE*"].isin(purposes)]

    # ── KPIs ──────────────────────────────────────────────────────────────────
    total_miles = fdf["MILES*"].sum() if "MILES*" in fdf.columns else 0
    avg_miles = fdf["MILES*"].mean() if "MILES*" in fdf.columns else 0
    avg_speed = fdf["SPEED"].dropna().mean() if "SPEED" in fdf.columns else 0
    avg_time = fdf["TRAVELLING_TIME"].dropna().mean() * 60 if "TRAVELLING_TIME" in fdf.columns else 0  # minutes

    kpi_row(st, [
        {"label": "Total Trips", "value": f"{len(fdf):,}"},
        {"label": "Total Miles", "value": f"{total_miles:,.0f}"},
        {"label": "Avg Miles/Trip", "value": f"{avg_miles:.1f}"},
        {"label": "Avg Trip Time", "value": f"{avg_time:.0f} min"},
        {"label": "Avg Speed", "value": f"{avg_speed:.1f} mph"},
        {"label": "Unique Purposes", "value": str(fdf["PURPOSE*"].nunique()) if "PURPOSE*" in fdf.columns else "—"},
    ])
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["🗂️ Overview", "⏰ Time Patterns", "📍 Locations", "🔬 Analysis"])

    # ── Tab 1: Overview ───────────────────────────────────────────────────────
    with tab1:
        col1, col2 = st.columns(2)

        if "CATEGORY*" in fdf.columns:
            cat_counts = fdf["CATEGORY*"].value_counts().reset_index()
            cat_counts.columns = ["Category", "Count"]
            with col1:
                st.plotly_chart(pie_chart(cat_counts, "Category", "Count", "Trip Category"),
                                use_container_width=True)

        if "PURPOSE*" in fdf.columns:
            purp_counts = fdf["PURPOSE*"].value_counts().reset_index()
            purp_counts.columns = ["Purpose", "Count"]
            with col2:
                st.plotly_chart(
                    bar_chart(purp_counts, "Purpose", "Count",
                              title="Trip Purpose", orientation="h"),
                    use_container_width=True
                )

        if "MILES*" in fdf.columns:
            st.plotly_chart(
                histogram(fdf, "MILES*", nbins=40,
                          color="CATEGORY*" if "CATEGORY*" in fdf.columns else None,
                          title="Distance Distribution (Miles)"),
                use_container_width=True
            )

    # ── Tab 2: Time Patterns ──────────────────────────────────────────────────
    with tab2:
        col1, col2 = st.columns(2)

        if "HOUR" in fdf.columns:
            hour_counts = fdf.groupby("HOUR").size().reset_index(name="Trips")
            with col1:
                fig = px.bar(hour_counts, x="HOUR", y="Trips",
                             title="Trips by Hour of Day", template="plotly_white",
                             color="Trips", color_continuous_scale="Blues")
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)

        if "WEEKDAY" in fdf.columns:
            wd_counts = fdf.groupby("WEEKDAY").size().reset_index(name="Trips")
            wd_counts["WEEKDAY"] = pd.Categorical(wd_counts["WEEKDAY"], categories=WEEKDAY_ORDER, ordered=True)
            wd_counts = wd_counts.sort_values("WEEKDAY")
            with col2:
                fig = px.bar(wd_counts, x="WEEKDAY", y="Trips",
                             title="Trips by Day of Week", template="plotly_white",
                             color="Trips", color_continuous_scale="Greens")
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)

        if "MONTH_NAME" in fdf.columns:
            m_counts = fdf.groupby("MONTH_NAME").size().reset_index(name="Trips")
            m_counts["MONTH_NAME"] = pd.Categorical(m_counts["MONTH_NAME"], categories=MONTH_ORDER, ordered=True)
            m_counts = m_counts.sort_values("MONTH_NAME")
            fig = px.line(m_counts, x="MONTH_NAME", y="Trips",
                          title="Trips by Month", template="plotly_white",
                          markers=True)
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

        # Heatmap: hour vs weekday
        if "HOUR" in fdf.columns and "WEEKDAY" in fdf.columns:
            heat_df = fdf.groupby(["WEEKDAY", "HOUR"]).size().reset_index(name="Trips")
            heat_pivot = heat_df.pivot(index="WEEKDAY", columns="HOUR", values="Trips").fillna(0)
            heat_pivot = heat_pivot.reindex([d for d in WEEKDAY_ORDER if d in heat_pivot.index])
            fig = px.imshow(heat_pivot, title="Trip Heatmap: Day × Hour",
                            template="plotly_white", color_continuous_scale="Blues",
                            text_auto=True, aspect="auto")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    # ── Tab 3: Locations ──────────────────────────────────────────────────────
    with tab3:
        col1, col2 = st.columns(2)

        if "START*" in fdf.columns:
            start_counts = fdf["START*"].value_counts().head(15).reset_index()
            start_counts.columns = ["Location", "Count"]
            with col1:
                st.plotly_chart(
                    bar_chart(start_counts, "Location", "Count",
                              title="Top 15 Start Locations", orientation="h"),
                    use_container_width=True
                )

        if "STOP*" in fdf.columns:
            stop_counts = fdf["STOP*"].value_counts().head(15).reset_index()
            stop_counts.columns = ["Location", "Count"]
            with col2:
                st.plotly_chart(
                    bar_chart(stop_counts, "Location", "Count",
                              title="Top 15 Stop Locations", orientation="h"),
                    use_container_width=True
                )

        # Miles by start location
        if "START*" in fdf.columns and "MILES*" in fdf.columns:
            loc_miles = fdf.groupby("START*")["MILES*"].mean().reset_index()
            loc_miles.columns = ["Start Location", "Avg Miles"]
            loc_miles = loc_miles.sort_values("Avg Miles", ascending=False).head(15)
            st.plotly_chart(
                bar_chart(loc_miles, "Start Location", "Avg Miles",
                          title="Avg Miles by Start Location"),
                use_container_width=True
            )

    # ── Tab 4: Analysis ───────────────────────────────────────────────────────
    with tab4:
        if "PURPOSE*" in fdf.columns and "MILES*" in fdf.columns:
            st.plotly_chart(
                box_plot(fdf, "PURPOSE*", "MILES*", title="Miles Distribution by Purpose"),
                use_container_width=True
            )

        # Purpose vs avg metrics
        if "PURPOSE*" in fdf.columns:
            grp_cols = ["MILES*", "TRAVELLING_TIME", "SPEED"]
            avail_grp = [c for c in grp_cols if c in fdf.columns]
            if avail_grp:
                purpose_stats = fdf.groupby("PURPOSE*")[avail_grp].mean().reset_index()
                purpose_stats.columns = ["Purpose"] + [c.replace("*", "").replace("_", " ").title()
                                                        for c in avail_grp]
                fig = px.bar(purpose_stats.melt("Purpose", var_name="Metric", value_name="Avg"),
                             x="Purpose", y="Avg", color="Metric", barmode="group",
                             title="Avg Metrics by Trip Purpose", template="plotly_white")
                fig.update_layout(height=420, xaxis_tickangle=-30)
                st.plotly_chart(fig, use_container_width=True)

        # Quick insights
        st.subheader("Quick Insights")
        if "CATEGORY*" in fdf.columns:
            top_cat = fdf["CATEGORY*"].value_counts().index[0]
            st.markdown(f"- **Most common category:** {top_cat}")
        if "PURPOSE*" in fdf.columns:
            top_purp = fdf["PURPOSE*"].value_counts().index[0]
            st.markdown(f"- **Most common purpose:** {top_purp}")
        if "WEEKDAY" in fdf.columns:
            busiest_day = fdf["WEEKDAY"].value_counts().index[0]
            st.markdown(f"- **Busiest day:** {busiest_day}")
        if "HOUR" in fdf.columns:
            peak_hour = fdf["HOUR"].value_counts().index[0]
            st.markdown(f"- **Peak hour:** {peak_hour}:00")
        if "MILES*" in fdf.columns:
            st.markdown(f"- **Most trips are short:** {(fdf['MILES*'] < 5).mean()*100:.1f}% under 5 miles")
        if "START*" in fdf.columns:
            top_start = fdf["START*"].value_counts().index[0]
            st.markdown(f"- **Most common start location:** {top_start}")
