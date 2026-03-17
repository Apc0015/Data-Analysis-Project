import streamlit as st
import sys, os

# Ensure utils/ is importable from all pages
sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="Data Analysis Hub",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #e8f0fe; }
[data-testid="stSidebar"] .stRadio > label { font-size: 15px; color: #1a1a2e; }
.block-container { padding-top: 1.5rem; }
h1 { color: #0066cc; }
h2 { color: #1a1a2e; }
.stMetric { background: #f0f4f8; border-radius: 8px; padding: 8px; border: 1px solid #d0dce8; }
.stTabs [data-baseweb="tab"] { font-size: 14px; font-weight: 600; color: #1a1a2e; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Data Analysis Hub")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        options=[
            "🏠 Home",
            "🦠 COVID-19",
            "₿ Cryptocurrency",
            "💣 Global Terrorism",
            "🎓 Universities",
            "👥 Demographics",
            "🚗 Uber Rides",
            "🍽️ Zomato",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("Live data: COVID-19, Crypto")
    st.caption("Static data: Terrorism, Universities, Demographics, Uber, Zomato")

# ── Page routing ──────────────────────────────────────────────────────────────
if page == "🏠 Home":
    st.title("📊 Data Analysis Hub")
    st.markdown(
        "An advanced multi-domain data analysis dashboard. "
        "Select a project from the sidebar to explore."
    )
    st.markdown("---")

    cards = [
        {
            "icon": "🦠", "title": "COVID-19 Global Dashboard",
            "desc": "Live global pandemic data — cases, deaths, recovery trends, country comparisons.",
            "tags": ["Live Data", "disease.sh API", "World Map"],
            "key": "covid",
        },
        {
            "icon": "₿", "title": "Cryptocurrency Markets",
            "desc": "Real-time prices, OHLC candlestick charts, multi-coin performance comparison.",
            "tags": ["Live Data", "CoinGecko API", "Candlestick"],
            "key": "crypto",
        },
        {
            "icon": "💣", "title": "Global Terrorism Analysis",
            "desc": "181,691 incidents from 1970–2017. Geo heatmaps, group analysis, attack trends.",
            "tags": ["CSV", "GTD Database", "1970–2017"],
            "key": "terrorism",
        },
        {
            "icon": "🎓", "title": "World University Rankings",
            "desc": "2,200 universities across 59 countries. Score metrics, radar charts, country benchmarks.",
            "tags": ["CSV", "CWUR Data", "2012–2015"],
            "key": "universities",
        },
        {
            "icon": "👥", "title": "Demographic Analysis",
            "desc": "48,842 adults census data. Income vs education, occupation, country patterns.",
            "tags": ["CSV", "UCI Adult Dataset", "Income"],
            "key": "demographics",
        },
        {
            "icon": "🚗", "title": "Uber Rides Analysis",
            "desc": "1,156 business trips. Time heatmaps, purpose breakdown, speed & distance stats.",
            "tags": ["CSV", "Trip Records", "2016"],
            "key": "uber",
        },
        {
            "icon": "🍽️", "title": "Zomato Restaurant Analysis",
            "desc": "55,569 restaurants across India. Ratings, cuisines, cost, city & location maps.",
            "tags": ["CSV", "Zomato India", "55K Restaurants"],
            "key": "zomato",
        },
    ]

    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]
    for i, card in enumerate(cards):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"### {card['icon']} {card['title']}")
                st.markdown(card["desc"])
                tags_html = " ".join(
                    [f'<span style="background:#dce8ff;color:#0044aa;border-radius:4px;padding:2px 8px;font-size:12px;margin-right:4px">{t}</span>'
                     for t in card["tags"]]
                )
                st.markdown(tags_html, unsafe_allow_html=True)

    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Dashboards", "7")
    col2.metric("Live Data Sources", "2")
    col3.metric("Static Datasets", "5")
    col4.metric("Total Records", "285,000+")

elif page == "🦠 COVID-19":
    from pages.covid import render
    render()

elif page == "₿ Cryptocurrency":
    from pages.crypto import render
    render()

elif page == "💣 Global Terrorism":
    from pages.terrorism import render
    render()

elif page == "🎓 Universities":
    from pages.universities import render
    render()

elif page == "👥 Demographics":
    from pages.demographics import render
    render()

elif page == "🚗 Uber Rides":
    from pages.uber import render
    render()

elif page == "🍽️ Zomato":
    from pages.zomato import render
    render()
