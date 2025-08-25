# beta_comparison

Streamlit app to view an HTML report either by uploading a file, entering a path, or using the repository default `corr_beta_MULTI_REPORT.html`.

## Running locally

1. Create a virtual environment and install dependencies.
2. Run the app.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploying on Streamlit Cloud

1. Push this repository to GitHub.
2. In Streamlit Cloud, create a new app pointing to this repo and select `app.py` as the entry point.
3. The app will install from `requirements.txt` and start automatically.

Notes:

- On Streamlit Cloud, the app defaults to "Embed (srcdoc)" mode for compatibility.
- If `corr_beta_MULTI_REPORT.html` is present in the repo root, the app will auto-load it on first open. Otherwise, upload an HTML file via the UI.
