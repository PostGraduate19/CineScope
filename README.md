# CineScope Fresh

A fresh, stable Streamlit movie recommender project with a flat dark-purple UI, TMDb poster + overview support, and Streamlit Community Cloud deployment readiness.

## Run locally
```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# Linux/macOS
source .venv/bin/activate
pip install -r requirements.txt
python src/build_model.py
streamlit run app.py
```

## TMDb key
Create a `.env` file in project root:
```env
TMDB_API_KEY=your_tmdb_api_key_here
```

For Streamlit Community Cloud, set:
```toml
TMDB_API_KEY = "your_tmdb_api_key_here"
```
