import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.data import load_demographics
from utils.charts import kpi_row, bar_chart, histogram, box_plot, heatmap, pie_chart


def render():
    st.title("👥 Demographic Data Analysis")
    st.caption("Dataset: UCI Adult Census Income — 48,842 individuals · Income classification: ≤50K vs >50K")

    with st.spinner("Loading dataset..."):
        df = load_demographics()

    if df.empty:
        st.error("Could not load demographics dataset.")
        return

    # Standardize income column
    inc_col = None
    for c in df.columns:
        if "income" in c.lower() or "salary" in c.lower():
            inc_col = c
            break

    # ── Sidebar filters ───────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### Filters")
        if "education" in df.columns:
            edus = st.multiselect("Education", sorted(df["education"].dropna().unique()), key="demo_edu")
        if "race" in df.columns:
            races = st.multiselect("Race", sorted(df["race"].dropna().unique()), key="demo_race")
        if "sex" in df.columns:
            genders = st.multiselect("Gender", sorted(df["sex"].dropna().unique()), key="demo_sex")

    fdf = df.copy()
    if "education" in df.columns and edus:
        fdf = fdf[fdf["education"].isin(edus)]
    if "race" in df.columns and races:
        fdf = fdf[fdf["race"].isin(races)]
    if "sex" in df.columns and genders:
        fdf = fdf[fdf["sex"].isin(genders)]

    # ── KPIs ──────────────────────────────────────────────────────────────────
    high_earners_pct = (fdf[inc_col].str.contains(">50K", na=False).sum() / len(fdf) * 100) if inc_col else 0
    avg_age = fdf["age"].mean() if "age" in fdf.columns else 0
    avg_hours = fdf["hours-per-week"].mean() if "hours-per-week" in fdf.columns else 0

    kpi_row(st, [
        {"label": "Total Records", "value": f"{len(fdf):,}"},
        {"label": "High Earners (>50K)", "value": f"{high_earners_pct:.1f}%"},
        {"label": "Avg Age", "value": f"{avg_age:.1f}"},
        {"label": "Avg Hours/Week", "value": f"{avg_hours:.1f}"},
        {"label": "Countries", "value": str(fdf["native-country"].nunique()) if "native-country" in fdf.columns else "—"},
        {"label": "Occupations", "value": str(fdf["occupation"].nunique()) if "occupation" in fdf.columns else "—"},
    ])
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["💰 Income", "📊 Demographics", "🎓 Education & Work", "🔬 Analysis"])

    # ── Tab 1: Income ─────────────────────────────────────────────────────────
    with tab1:
        col1, col2 = st.columns(2)

        if inc_col:
            inc_counts = fdf[inc_col].value_counts().reset_index()
            inc_counts.columns = ["Income", "Count"]
            with col1:
                st.plotly_chart(pie_chart(inc_counts, "Income", "Count", "Income Distribution"),
                                use_container_width=True)

        if inc_col and "education" in fdf.columns:
            edu_inc = fdf.groupby(["education", inc_col]).size().reset_index(name="Count")
            with col2:
                fig = px.bar(edu_inc, x="education", y="Count", color=inc_col,
                             barmode="group", title="Income by Education Level",
                             template="plotly_white")
                fig.update_layout(height=380, xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

        if inc_col and "occupation" in fdf.columns:
            occ_inc = fdf.groupby("occupation")[inc_col].apply(
                lambda x: (x.str.contains(">50K", na=False).sum() / len(x) * 100)
            ).reset_index()
            occ_inc.columns = ["Occupation", "High Earner %"]
            occ_inc = occ_inc.sort_values("High Earner %", ascending=True)
            fig = px.bar(occ_inc, x="High Earner %", y="Occupation", orientation="h",
                         title="High Earner % by Occupation", template="plotly_white",
                         color="High Earner %", color_continuous_scale="Viridis")
            fig.update_layout(height=420)
            st.plotly_chart(fig, use_container_width=True)

    # ── Tab 2: Demographics ───────────────────────────────────────────────────
    with tab2:
        col1, col2 = st.columns(2)

        if "race" in fdf.columns:
            race_counts = fdf["race"].value_counts().reset_index()
            race_counts.columns = ["Race", "Count"]
            with col1:
                st.plotly_chart(pie_chart(race_counts, "Race", "Count", "Race Distribution"),
                                use_container_width=True)

        if "sex" in fdf.columns:
            sex_counts = fdf["sex"].value_counts().reset_index()
            sex_counts.columns = ["Gender", "Count"]
            with col2:
                st.plotly_chart(pie_chart(sex_counts, "Gender", "Count", "Gender Distribution"),
                                use_container_width=True)

        if "age" in fdf.columns:
            color_arg = inc_col if inc_col else None
            st.plotly_chart(
                histogram(fdf, "age", nbins=30, color=color_arg, title="Age Distribution by Income"),
                use_container_width=True
            )

        if "race" in fdf.columns and inc_col:
            race_inc = fdf.groupby("race")[inc_col].apply(
                lambda x: (x.str.contains(">50K", na=False).sum() / len(x) * 100)
            ).reset_index()
            race_inc.columns = ["Race", "High Earner %"]
            st.plotly_chart(
                bar_chart(race_inc.sort_values("High Earner %", ascending=False),
                          "Race", "High Earner %", title="High Earner % by Race"),
                use_container_width=True
            )

    # ── Tab 3: Education & Work ───────────────────────────────────────────────
    with tab3:
        col1, col2 = st.columns(2)

        if "education" in fdf.columns:
            edu_counts = fdf["education"].value_counts().reset_index()
            edu_counts.columns = ["Education", "Count"]
            with col1:
                st.plotly_chart(
                    bar_chart(edu_counts, "Education", "Count",
                              title="Education Level Distribution", orientation="h"),
                    use_container_width=True
                )

        if "hours-per-week" in fdf.columns and inc_col:
            with col2:
                st.plotly_chart(
                    box_plot(fdf, inc_col, "hours-per-week",
                             title="Hours/Week by Income"),
                    use_container_width=True
                )

        if "native-country" in fdf.columns and inc_col:
            country_high = fdf.groupby("native-country")[inc_col].apply(
                lambda x: (x.str.contains(">50K", na=False).sum() / len(x) * 100)
            ).reset_index()
            country_high.columns = ["Country", "High Earner %"]
            country_high = country_high[country_high["Country"] != "?"]
            country_high = country_high.sort_values("High Earner %", ascending=False).head(20)
            st.plotly_chart(
                bar_chart(country_high, "Country", "High Earner %",
                          title="Top 20 Countries — High Earner %"),
                use_container_width=True
            )

    # ── Tab 4: Analysis ───────────────────────────────────────────────────────
    with tab4:
        numeric = fdf.select_dtypes(include="number")
        if not numeric.empty and numeric.shape[1] >= 2:
            st.plotly_chart(heatmap(numeric.corr(), "Correlation Matrix"), use_container_width=True)

        # Education vs Age vs Income bubble
        if "age" in fdf.columns and "hours-per-week" in fdf.columns and "education" in fdf.columns:
            fig = px.scatter(
                fdf.sample(min(3000, len(fdf))),
                x="age", y="hours-per-week",
                color=inc_col if inc_col else "education",
                facet_col="sex" if "sex" in fdf.columns else None,
                title="Age vs Hours/Week by Income & Gender",
                template="plotly_white",
                opacity=0.5,
            )
            fig.update_layout(height=420)
            st.plotly_chart(fig, use_container_width=True)

        # Quick insights
        st.subheader("Quick Insights")
        if inc_col:
            higher_edu = ["Bachelors", "Masters", "Doctorate", "Prof-school"]
            higher = fdf[fdf.get("education", pd.Series()).isin(higher_edu)][inc_col] if "education" in fdf.columns else pd.Series()
            lower = fdf[~fdf.get("education", pd.Series(dtype=str)).isin(higher_edu)][inc_col] if "education" in fdf.columns else pd.Series()
            if len(higher) > 0:
                h_pct = higher.str.contains(">50K", na=False).mean() * 100
                st.markdown(f"- **Higher education high earners:** {h_pct:.1f}%")
            if len(lower) > 0:
                l_pct = lower.str.contains(">50K", na=False).mean() * 100
                st.markdown(f"- **Without higher education high earners:** {l_pct:.1f}%")
        if "sex" in fdf.columns and inc_col:
            for g in fdf["sex"].dropna().unique():
                pct = fdf[fdf["sex"] == g][inc_col].str.contains(">50K", na=False).mean() * 100
                st.markdown(f"- **{g} high earners:** {pct:.1f}%")
