# pgis

Streamlit app for Railway.

Railway start command:

```bash
python -m streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT:-8501} --server.headless=true --browser.gatherUsageStats=false
```

Deploy notes:

- Keep `app.py`, `requirements.txt`, `railway.json`, `Procfile`, and `.python-version` in the project root.
- In Railway, generate a public domain from Settings > Networking > Public Networking.
- Optional: set `MAPBOX_TOKEN` or `NEXT_PUBLIC_MAPBOX_TOKEN` in Railway variables. Without it, the app falls back to Carto map tiles.
