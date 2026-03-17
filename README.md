# 📊 DataFlow Analytics — Multi-Project Data Analysis Dashboard

A unified Streamlit dashboard combining **7 data analysis projects** with live APIs and static datasets, interactive Plotly charts, and advanced Jupyter notebooks.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://data-analysis-project-afb4kdjxzj4jjsqvfahuzt.streamlit.app/)

---

## 🚀 Live Demo

**[https://data-analysis-project-afb4kdjxzj4jjsqvfahuzt.streamlit.app/](https://data-analysis-project-afb4kdjxzj4jjsqvfahuzt.streamlit.app/)**

---

## 📁 Projects

| # | Project | Data Source | Records | Type |
|---|---------|------------|---------|------|
| 1 | 🦠 COVID-19 Global Tracker | disease.sh API (live) | 209 countries | Live |
| 2 | 💰 Cryptocurrency Dashboard | CoinGecko API (live) | Real-time prices | Live |
| 3 | 💣 Global Terrorism Analysis | GTD CSV (1970–2017) | 181,691 incidents | Static |
| 4 | 🎓 World University Rankings | CWUR CSV | 2,200 universities | Static |
| 5 | 👥 Demographics & Income | UCI Adult Census CSV | 48,842 individuals | Static |
| 6 | 🚗 Uber Rides Analysis | Uber Trips CSV | 1,156 trips | Static |
| 7 | 🍽️ Zomato Restaurant Analysis | Zomato India CSV | 55,569 restaurants | Static |

---

## 🗂️ Project Structure

```
Data-Analysis-Project/
├── streamlit_app/              # Main Streamlit application
│   ├── app.py                  # Entry point & navigation
│   ├── pages/                  # One file per dashboard
│   │   ├── covid.py
│   │   ├── crypto.py
│   │   ├── terrorism.py
│   │   ├── universities.py
│   │   ├── demographics.py
│   │   ├── uber.py
│   │   └── zomato.py
│   └── utils/
│       ├── data.py             # All data loaders (API + CSV)
│       └── charts.py           # Reusable Plotly chart helpers
│
├── projects/                   # Organised project data & notebooks
│   ├── covid19/notebooks/      # covid_advanced.ipynb
│   ├── cryptocurrency/notebooks/ # crypto_advanced.ipynb
│   ├── terrorism/notebooks/    # terrorism_advanced.ipynb
│   ├── universities/data/      # cwurData.csv
│   │             /notebooks/   # universities_advanced.ipynb
│   ├── demographics/data/      # adult.csv
│   │              /notebooks/  # demographics_advanced.ipynb
│   ├── uber/data/              # uber_trips.csv
│   │     /notebooks/           # uber_advanced.ipynb
│   └── zomato/data/            # ZOMATO_FINAL.csv
│          /notebooks/          # zomato_advanced.ipynb
│
├── .streamlit/config.toml      # Light theme configuration
├── requirements.txt
└── README.md
```

---

## ⚙️ Run Locally

```bash
git clone https://github.com/Apc0015/Data-Analysis-Project.git
cd Data-Analysis-Project

python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

pip install -r requirements.txt
streamlit run streamlit_app/app.py
```

> **Note:** The Global Terrorism CSV (`globalterrorismdb_utf8.csv`, 155MB) is excluded from git due to GitHub's file size limit. Download it from [Kaggle — Global Terrorism Database](https://www.kaggle.com/datasets/START-UMD/gtd) and place it at `projects/terrorism/data/globalterrorismdb_utf8.csv`.

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit 1.32+
- **Charts:** Plotly Express & Graph Objects
- **Data:** Pandas, NumPy
- **Live APIs:** disease.sh (COVID-19), CoinGecko (Crypto)
- **Analysis:** SciPy, Statsmodels

---

## 📓 Jupyter Notebooks

Each project has an advanced analysis notebook in `projects/{name}/notebooks/`:

- [`covid_advanced.ipynb`](projects/covid19/notebooks/covid_advanced.ipynb) — Time-series forecasting, mortality analysis
- [`crypto_advanced.ipynb`](projects/cryptocurrency/notebooks/crypto_advanced.ipynb) — OHLC analysis, volatility, correlation
- [`terrorism_advanced.ipynb`](projects/terrorism/notebooks/terrorism_advanced.ipynb) — Geospatial clustering, trend analysis
- [`universities_advanced.ipynb`](projects/universities/notebooks/universities_advanced.ipynb) — Ranking factors, country comparison
- [`demographics_advanced.ipynb`](projects/demographics/notebooks/demographics_advanced.ipynb) — Income prediction, feature importance
- [`uber_advanced.ipynb`](projects/uber/notebooks/uber_advanced.ipynb) — Trip pattern analysis, time series
- [`zomato_advanced.ipynb`](projects/zomato/notebooks/zomato_advanced.ipynb) — Cuisine trends, rating analysis

---

## 🌐 Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. New app → select this repo → set **Main file path:** `streamlit_app/app.py`
3. Deploy

---

*Built with ❤️ using Streamlit & Plotly*
