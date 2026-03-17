import io
import time
import requests
import pandas as pd
import streamlit as st

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DataFlowAnalytics/1.0)",
    "Accept": "application/json",
}


def _get(url, retries=3, **kwargs):
    """requests.get with retries and back-off on 429."""
    kwargs.setdefault("timeout", 20)
    kwargs.setdefault("headers", _HEADERS)
    for attempt in range(retries):
        r = requests.get(url, **kwargs)
        if r.status_code == 429:
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
        return r
    r.raise_for_status()
    return r

# ── COVID-19 (disease.sh) ────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_covid_world():
    """All countries — latest totals."""
    try:
        r = _get("https://disease.sh/v3/covid-19/countries?yesterday=false&sort=cases")
        data = r.json()
        df = pd.json_normalize(data)
        df = df.rename(columns={
            "country": "Country",
            "cases": "Total Cases",
            "deaths": "Total Deaths",
            "recovered": "Recovered",
            "active": "Active",
            "todayCases": "Today Cases",
            "todayDeaths": "Today Deaths",
            "todayRecovered": "Today Recovered",
            "critical": "Critical",
            "casesPerOneMillion": "Cases/1M",
            "deathsPerOneMillion": "Deaths/1M",
            "tests": "Tests",
            "testsPerOneMillion": "Tests/1M",
            "population": "Population",
            "continent": "Continent",
            "countryInfo.lat": "Lat",
            "countryInfo.long": "Lon",
        })
        keep = ["Country", "Continent", "Population", "Total Cases", "Total Deaths",
                "Recovered", "Active", "Today Cases", "Today Deaths", "Today Recovered",
                "Critical", "Cases/1M", "Deaths/1M", "Tests", "Tests/1M", "Lat", "Lon"]
        df = df[[c for c in keep if c in df.columns]]
        df["Mortality Rate (%)"] = (df["Total Deaths"] / df["Total Cases"] * 100).round(2)
        df["Recovery Rate (%)"] = (df["Recovered"] / df["Total Cases"] * 100).round(2)
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_covid_global():
    """Single global summary row."""
    try:
        r = _get("https://disease.sh/v3/covid-19/all")
        return r.json()
    except Exception:
        return {}


@st.cache_data(ttl=3600)
def load_covid_historical(country="all", days=90):
    """Historical timeline for a country or 'all'."""
    try:
        url = f"https://disease.sh/v3/covid-19/historical/{country}?lastdays={days}"
        r = _get(url)
        data = r.json()
        timeline = data.get("timeline", data)
        cases = pd.Series(timeline.get("cases", {}), name="Cases")
        deaths = pd.Series(timeline.get("deaths", {}), name="Deaths")
        recovered = pd.Series(timeline.get("recovered", {}), name="Recovered")
        df = pd.concat([cases, deaths, recovered], axis=1).reset_index()
        df.columns = ["Date", "Cases", "Deaths", "Recovered"]
        df["Date"] = pd.to_datetime(df["Date"])
        df["Daily Cases"] = df["Cases"].diff().clip(lower=0)
        df["Daily Deaths"] = df["Deaths"].diff().clip(lower=0)
        return df
    except Exception:
        return pd.DataFrame()


# ── Cryptocurrency (CoinGecko) ───────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_crypto_prices(coin_ids="bitcoin,ethereum,dogecoin,solana,binancecoin"):
    """Current prices + 24h change."""
    try:
        url = (
            "https://api.coingecko.com/api/v3/coins/markets"
            f"?vs_currency=usd&ids={coin_ids}"
            "&order=market_cap_desc&per_page=20&page=1"
            "&sparkline=false&price_change_percentage=24h,7d,30d"
        )
        r = _get(url)
        df = pd.json_normalize(r.json())
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_crypto_history(coin_id="bitcoin", days=90):
    """OHLC + volume history for a coin."""
    try:
        url = (
            f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
            f"?vs_currency=usd&days={days}"
        )
        r = _get(url)
        data = r.json()
        df = pd.DataFrame(data, columns=["timestamp", "Open", "High", "Low", "Close"])
        df["Date"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df[["Date", "Open", "High", "Low", "Close"]]
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_crypto_market_chart(coin_id="bitcoin", days=90):
    """Price + volume time series."""
    try:
        url = (
            f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
            f"?vs_currency=usd&days={days}"
        )
        r = _get(url)
        data = r.json()
        prices = pd.DataFrame(data["prices"], columns=["ts", "Price"])
        volumes = pd.DataFrame(data["total_volumes"], columns=["ts", "Volume"])
        df = prices.merge(volumes, on="ts")
        df["Date"] = pd.to_datetime(df["ts"], unit="ms")
        return df[["Date", "Price", "Volume"]]
    except Exception:
        return pd.DataFrame()


# ── Static CSV loaders ────────────────────────────────────────────────────────

def _read_csv(path, **kwargs):
    import os
    if not os.path.exists(path):
        return pd.DataFrame()
    for enc in ["utf-8", "latin1", "iso-8859-1", "cp1252"]:
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except Exception:
            continue
    try:
        return pd.read_csv(path, encoding="utf-8", errors="replace", **kwargs)
    except Exception:
        return pd.DataFrame()


@st.cache_data
def load_terrorism():
    import os
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    path = os.path.join(base, "projects", "terrorism", "data", "globalterrorismdb_utf8.csv")
    cols = ["iyear", "imonth", "iday", "country_txt", "region_txt", "city",
            "latitude", "longitude", "attacktype1_txt", "targtype1_txt",
            "gname", "nkill", "nwound", "success"]
    df = _read_csv(path, usecols=cols, low_memory=False)
    df = df.rename(columns={
        "iyear": "Year", "imonth": "Month", "iday": "Day",
        "country_txt": "Country", "region_txt": "Region", "city": "City",
        "latitude": "Lat", "longitude": "Lon",
        "attacktype1_txt": "Attack Type", "targtype1_txt": "Target Type",
        "gname": "Group", "nkill": "Killed", "nwound": "Wounded", "success": "Success"
    })
    df["Killed"] = pd.to_numeric(df["Killed"], errors="coerce").fillna(0)
    df["Wounded"] = pd.to_numeric(df["Wounded"], errors="coerce").fillna(0)
    df["Casualties"] = df["Killed"] + df["Wounded"]
    return df


@st.cache_data
def load_universities():
    import os
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    path = os.path.join(base, "projects", "universities", "data", "cwurData.csv")
    df = _read_csv(path)
    return df


@st.cache_data
def load_demographics():
    import os
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    path = os.path.join(base, "projects", "demographics", "data", "adult.csv")
    df = _read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    # strip string values
    for c in df.select_dtypes("object").columns:
        df[c] = df[c].str.strip()
    return df


@st.cache_data
def load_uber():
    import os
    import calendar
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    path = os.path.join(base, "projects", "uber", "data", "uber_trips.csv")
    df = _read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    df["START_DATE*"] = pd.to_datetime(df["START_DATE*"], format="%m/%d/%Y %H:%M", errors="coerce")
    df["END_DATE*"] = pd.to_datetime(df["END_DATE*"], format="%m/%d/%Y %H:%M", errors="coerce")
    df = df.dropna(subset=["START_DATE*", "END_DATE*"])
    df["HOUR"] = df["START_DATE*"].dt.hour
    df["DAY"] = df["START_DATE*"].dt.day
    df["DAY_OF_WEEK"] = df["START_DATE*"].dt.dayofweek
    df["MONTH"] = df["START_DATE*"].dt.month
    df["WEEKDAY"] = df["START_DATE*"].dt.day_name()
    df["MONTH_NAME"] = df["START_DATE*"].dt.month_name()
    travelling_time = (df["END_DATE*"] - df["START_DATE*"]).dt.seconds / 3600  # hours
    travelling_time = travelling_time.replace(0, float("nan"))
    df["TRAVELLING_TIME"] = travelling_time
    df["MILES*"] = pd.to_numeric(df["MILES*"], errors="coerce")
    df["SPEED"] = df["MILES*"] / df["TRAVELLING_TIME"]
    return df


# ── Zomato ────────────────────────────────────────────────────────────────────

@st.cache_data
def load_zomato():
    import os
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    path = os.path.join(base, "projects", "zomato", "data", "ZOMATO_FINAL.csv")
    df = _read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    df["aggregate_rating"] = pd.to_numeric(df["aggregate_rating"], errors="coerce")
    df["average_cost_for_two"] = pd.to_numeric(df["average_cost_for_two"], errors="coerce")
    df["votes"] = pd.to_numeric(df["votes"], errors="coerce")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    return df
