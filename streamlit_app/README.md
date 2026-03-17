# Data Projects Hub (Streamlit)

Run this app from the workspace root:

```
pip install -r streamlit_app/requirements.txt
streamlit run streamlit_app/app.py
```

What it does:
- Discovers top-level folders containing `.csv` or `.ipynb` files
- Lets you preview CSVs, view summary stats, and create simple plots
- Renders notebook markdown and code cells for quick browsing

Next steps:
- Add custom pages per project
- Add caching for large CSV loads
