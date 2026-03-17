import yfinance as yf
import pandas as pd
import altair as alt


def render(st, project_path):
    st.header('Cryptocurrency Live Dashboard')
    cfg_path = project_path + '/project_config.json'
    tickers = ['BTC-USD', 'ETH-USD']
    try:
        import json
        with open(cfg_path, 'r', encoding='utf-8') as fh:
            cfg = json.load(fh)
        # allow config to specify tickers
        for src in cfg.get('data_sources', []):
            if src.get('type') == 'crypto_tickers' and 'tickers' in src:
                tickers = src['tickers']
    except Exception:
        pass

    st.write(f'Watching tickers: {", ".join(tickers)}')

    cols = st.columns(len(tickers))
    for i, t in enumerate(tickers):
        with cols[i]:
            try:
                tk = yf.Ticker(t)
                hist = tk.history(period='7d', interval='1h')
                if hist.empty:
                    st.info(f'No recent data for {t}')
                    continue
                price = hist['Close'].iloc[-1]
                change = (price - hist['Close'].iloc[0]) / hist['Close'].iloc[0]
                st.metric(t, f"{price:.2f}", f"{change*100:.2f}%")
            except Exception as e:
                st.error(f'Failed to fetch {t}: {e}')

    st.subheader('Charts')
    # combined chart for the first two tickers
    combined = []
    for t in tickers[:3]:
        try:
            hist = yf.Ticker(t).history(period='30d', interval='1d')
            df = hist.reset_index()[['Date', 'Close']].rename(columns={'Close': t})
            combined.append(df.set_index('Date'))
        except Exception:
            continue
    if combined:
        dfc = pd.concat(combined, axis=1).reset_index()
        dfm = dfc.melt(id_vars='Date', var_name='ticker', value_name='close')
        chart = alt.Chart(dfm).mark_line().encode(x='Date:T', y='close:Q', color='ticker:N', tooltip=['ticker', 'close'])
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info('No chart data available.')
