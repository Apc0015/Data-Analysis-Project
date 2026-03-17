import os
from pathlib import Path
import pandas as pd
import streamlit as st
import altair as alt
import numpy as np
import json
import io
import requests


def find_projects(base_dir: str):
    projects = []
    for name in sorted(os.listdir(base_dir)):
        path = os.path.join(base_dir, name)
        if not os.path.isdir(path):
            continue
        if name.startswith('.') or name == 'streamlit_app':
            continue
        # check for csv or ipynb inside
        has_data = False
        for root, _, files in os.walk(path):
            for f in files:
                if f.lower().endswith(('.csv', '.ipynb')):
                    has_data = True
                    break
            if has_data:
                break
        if has_data:
            projects.append({'name': name, 'path': path})
    return projects


def list_files(project_path, exts):
    files = []
    for root, _, filenames in os.walk(project_path):
        for f in filenames:
            if f.lower().endswith(exts):
                rel = os.path.relpath(os.path.join(root, f), project_path)
                files.append({'name': rel, 'full': os.path.join(root, f)})
    return sorted(files, key=lambda x: x['name'])


def read_project_config(project_path):
    cfg_json = os.path.join(project_path, 'project_config.json')
    if os.path.exists(cfg_json):
        try:
            with open(cfg_json, 'r', encoding='utf-8') as fh:
                return json.load(fh)
        except Exception:
            return None
    return None


@st.cache_data
def load_csv(path):
    # try common encodings when reading local CSVs
    encs = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
    for e in encs:
        try:
            return pd.read_csv(path, encoding=e)
        except Exception:
            continue
    # last resort, let pandas infer with errors='replace'
    return pd.read_csv(path, encoding='utf-8', errors='replace')


@st.cache_data
def load_remote_csv(url: str):
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return pd.read_csv(io.StringIO(r.text))
    except Exception:
        return pd.DataFrame()


def read_readme(project_path):
    p = Path(project_path) / 'README.md'
    if p.exists():
        try:
            text = p.read_text(encoding='utf-8')
            first = '\n'.join([l for l in text.splitlines() if l.strip()][:6])
            return first
        except Exception:
            return ''
    return ''


def summarize_df(df: pd.DataFrame):
    num_rows, num_cols = df.shape
    missing = df.isna().sum().sort_values(ascending=False)
    missing_pct = (missing / num_rows * 100).round(2)
    numeric = df.select_dtypes(include=['number'])
    top_numeric = numeric.var().sort_values(ascending=False).head(5).index.tolist()
    categorical = df.select_dtypes(include=['object', 'category']).columns.tolist()
    return {
        'rows': int(num_rows),
        'cols': int(num_cols),
        'missing': missing.to_dict(),
        'missing_pct': missing_pct.to_dict(),
        'top_numeric': top_numeric,
        'categorical': categorical,
    }


def project_card(col, project):
    desc = read_readme(project['path'])
    with col:
        st.subheader(project['name'])
        if desc:
            st.write(desc)
        csvs = list_files(project['path'], ('.csv',))
        ipynbs = list_files(project['path'], ('.ipynb',))
        st.markdown(f"**Datasets:** {len(csvs)} &nbsp;&middot;&nbsp; **Notebooks:** {len(ipynbs)}")
        if st.button('Open Dashboard', key=f"open-{project['name']}"):
            st.session_state['project'] = project['name']


def show_project_dashboard(project):
    st.header(project['name'])
    desc = read_readme(project['path'])
    if desc:
        st.markdown(desc)

    # Check project config for live data sources
    cfg = read_project_config(project['path'])
    datasets = []
    if cfg and 'data_sources' in cfg:
        for src in cfg['data_sources']:
            datasets.append({'name': src.get('name', src.get('path')), 'source': src})
    else:
        csv_files = list_files(project['path'], ('.csv',))
        if not csv_files:
            st.info('No CSV datasets found for this project.')
            return
        datasets = [{'name': f['name'], 'source': {'type': 'local_csv', 'path': f['full']}} for f in csv_files]

    selected = st.selectbox('Select dataset', [d['name'] for d in datasets])
    dataset = next(d for d in datasets if d['name'] == selected)

    src = dataset['source']
    df = pd.DataFrame()
    if src.get('type') == 'remote_csv' and src.get('path'):
        refresh = int(src.get('refresh_seconds', 300))
        # use cache with TTL by invalidating key using refresh value
        @st.cache_data(ttl=refresh)
        def _load_remote(url):
            return load_remote_csv(url)

        df = _load_remote(src['path'])
    elif src.get('type') == 'local_csv' and src.get('path'):
        df = load_csv(src['path'])
    else:
        # fallback: try path or URL
        path = src.get('path')
        if path and str(path).lower().startswith('http'):
            df = load_remote_csv(path)
        elif path:
            df = load_csv(path)
    summary = summarize_df(df)

    col1, col2, col3 = st.columns(3)
    col1.metric('Rows', summary['rows'])
    col2.metric('Columns', summary['cols'])
    missing_total = sum(v for v in summary['missing'].values())
    col3.metric('Total missing', int(missing_total))

    st.markdown('---')

    # Missing values bar
    miss = pd.Series(summary['missing_pct']).rename('missing_pct').reset_index()
    miss.columns = ['column', 'missing_pct']
    if not miss.empty:
        chart = alt.Chart(miss).mark_bar().encode(x=alt.X('missing_pct:Q'), y=alt.Y('column:N', sort='-x'))
        st.altair_chart(chart, use_container_width=True)

    numeric = df.select_dtypes(include=['number']).columns.tolist()
    if numeric:
        st.subheader('Automatic Visualizations')
        # Top numeric histogram
        top_num = summary['top_numeric'][0] if summary['top_numeric'] else numeric[0]
        st.markdown(f'**Distribution — {top_num}**')
        hist = alt.Chart(df).mark_bar().encode(x=alt.X(top_num, bin=alt.Bin(maxbins=40)), y='count()')
        st.altair_chart(hist, use_container_width=True)

        # Scatter of top two numeric
        if len(summary['top_numeric']) >= 2:
            xcol, ycol = summary['top_numeric'][:2]
            st.markdown(f'**Scatter — {xcol} vs {ycol}**')
            scatter = alt.Chart(df).mark_circle(size=60).encode(x=xcol, y=ycol, tooltip=numeric)
            st.altair_chart(scatter, use_container_width=True)
    else:
        st.info('No numeric columns to visualize.')

    # Show top categories for categorical columns
    if summary['categorical']:
        st.subheader('Top categories')
        for c in summary['categorical'][:3]:
            counts = df[c].value_counts().nlargest(10).reset_index()
            counts.columns = [c, 'count']
            bar = alt.Chart(counts).mark_bar().encode(x='count:Q', y=alt.Y(f'{c}:N', sort='-x'))
            st.markdown(f'**{c}**')
            st.altair_chart(bar, use_container_width=True)

    # Support per-project custom dashboard script
    custom_path = os.path.join(project['path'], 'project_dashboard.py')
    if os.path.exists(custom_path):
        st.markdown('---')
        st.subheader('Project Custom Dashboard')
        st.write('This project includes a custom dashboard script: `project_dashboard.py`.')
        if st.button('Open custom project dashboard'):
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(f"custom_{project['name']}", custom_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, 'render'):
                    mod.render(st, project['path'])
                else:
                    st.info('Custom dashboard loaded, but no `render(st, project_path)` function found.')
            except Exception as e:
                st.error(f'Failed to run custom dashboard: {e}')

    # Additional automated insights
    st.markdown('---')
    st.subheader('Automated Insights')
    
    def correlation_heatmap(df):
        corr = df.corr()
        if corr.empty:
            st.info('Not enough numeric columns for correlation matrix.')
            return
        corr_long = corr.reset_index().melt(id_vars='index')
        corr_long.columns = ['x', 'y', 'value']
        heat = alt.Chart(corr_long).mark_rect().encode(
            x=alt.X('x:N', sort=None),
            y=alt.Y('y:N', sort=None),
            color=alt.Color('value:Q', scale=alt.Scale(scheme='redblue')),
            tooltip=['x', 'y', alt.Tooltip('value:Q', format='.2f')]
        )
        st.markdown('**Correlation matrix**')
        st.altair_chart(heat.configure_axis(labelAngle=0), use_container_width=True)

    def detect_outliers(df):
        num = df.select_dtypes(include=['number'])
        outlier_counts = {}
        for c in num.columns:
            series = num[c].dropna()
            if series.empty:
                continue
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            cnt = int(((series < lower) | (series > upper)).sum())
            outlier_counts[c] = cnt
        return outlier_counts

    def auto_text_insights(df, summary):
        insights = []
        # Missingness
        missing = summary['missing_pct']
        if missing:
            top_miss = sorted(missing.items(), key=lambda x: x[1], reverse=True)[:3]
            insights.append('Highest missing: ' + ', '.join([f"{k} ({v}%)" for k, v in top_miss]))
        # Correlations
        num = df.select_dtypes(include=['number'])
        if num.shape[1] >= 2:
            corr = num.corr().abs()
            # find top correlated pair
            corr_unstack = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack()
            if not corr_unstack.empty:
                top_pair = corr_unstack.idxmax()
                top_val = corr_unstack.max()
                insights.append(f"Top correlation: {top_pair[0]} & {top_pair[1]} ({top_val:.2f})")
        # Outliers
        out = detect_outliers(df)
        if out:
            top_out = sorted(out.items(), key=lambda x: x[1], reverse=True)[:3]
            insights.append('Most outliers: ' + ', '.join([f"{k} ({v})" for k, v in top_out if v > 0]))
        return insights

    # compute and show
    try:
        correlation_heatmap(df.select_dtypes(include=['number']))
    except Exception:
        st.info('Unable to compute correlation matrix.')

    outliers = detect_outliers(df)
    if outliers:
        out_summary = pd.Series(outliers).sort_values(ascending=False).head(5)
        st.markdown('**Outlier counts (top 5 numeric cols)**')
        st.table(out_summary)

    insights = auto_text_insights(df, summary)
    if insights:
        st.markdown('**Quick insights**')
        for i in insights:
            st.write('- ' + i)


def main():
    st.set_page_config(page_title='Data Projects Hub', layout='wide')
    st.title('Data Projects Hub')

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    projects = find_projects(base_dir)

    if 'project' not in st.session_state:
        st.session_state['project'] = None

    if not projects:
        st.warning('No projects with CSV or notebooks found in workspace root.')
        st.stop()

    if st.session_state['project'] is None:
        st.markdown('## Projects')
        cols = st.columns(3)
        for i, p in enumerate(projects):
            project_card(cols[i % 3], p)
    else:
        proj = next((p for p in projects if p['name'] == st.session_state['project']), None)
        if proj is None:
            st.error('Selected project not found')
            st.session_state['project'] = None
        else:
            if st.button('Back to projects'):
                st.session_state['project'] = None
            show_project_dashboard(proj)


if __name__ == '__main__':
    main()
