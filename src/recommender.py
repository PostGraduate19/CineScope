from pathlib import Path
import json
import os
import pickle
import pandas as pd
import requests
from dotenv import load_dotenv
from sklearn.metrics.pairwise import linear_kernel
from src.build_model import download_dataset, build_artifacts

load_dotenv()

BASE = Path(__file__).resolve().parents[1]
MODEL_DIR = BASE / "models"
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
TMDB_MOVIE_URL = "https://api.themoviedb.org/3/movie/{tmdb_id}"
CACHE_FILE = MODEL_DIR / "poster_cache.json"


def ensure_artifacts():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    movies_file = MODEL_DIR / "movies.pkl"
    genre_file = MODEL_DIR / "genre_matrix.pkl"
    index_file = MODEL_DIR / "title_to_index.json"
    cache_file = MODEL_DIR / "poster_cache.json"

    if movies_file.exists() and genre_file.exists() and index_file.exists():
        if not cache_file.exists():
            cache_file.write_text("{}", encoding="utf-8")
        return

    download_dataset()
    build_artifacts()

    if not cache_file.exists():
        cache_file.write_text("{}", encoding="utf-8")


ensure_artifacts()

with open(MODEL_DIR / "movies.pkl", "rb") as f:
    movies = pickle.load(f)

with open(MODEL_DIR / "genre_matrix.pkl", "rb") as f:
    genre_matrix = pickle.load(f)

with open(MODEL_DIR / "title_to_index.json", "r", encoding="utf-8") as f:
    title_to_index = json.load(f)


def _load_cache():
    if CACHE_FILE.exists():
        try:
            data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def _save_cache(cache):
    CACHE_FILE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def get_api_key(streamlit_secrets=None):
    if TMDB_API_KEY:
        return TMDB_API_KEY

    if streamlit_secrets:
        try:
            return streamlit_secrets["TMDB_API_KEY"]
        except Exception:
            return ""

    return ""


def short_overview(text, limit=150):
    if not text:
        return "No summary available."

    text = " ".join(str(text).split())

    if len(text) <= limit:
        return text

    return text[:limit].rsplit(" ", 1)[0] + "..."


def get_movie_details(tmdb_id, streamlit_secrets=None):
    api_key = get_api_key(streamlit_secrets)

    if not api_key or pd.isna(tmdb_id):
        return {"poster_url": None, "overview": None}

    cache = _load_cache()
    key = str(int(tmdb_id))
    cached = cache.get(key)

    if isinstance(cached, dict):
        return {
            "poster_url": cached.get("poster_url"),
            "overview": cached.get("overview"),
        }

    try:
        url = TMDB_MOVIE_URL.format(tmdb_id=int(tmdb_id))
        r = requests.get(url, params={"api_key": api_key}, timeout=10)

        if r.status_code != 200:
            result = {"poster_url": None, "overview": None}
            cache[key] = result
            _save_cache(cache)
            return result

        data = r.json()
        poster_path = data.get("poster_path")
        overview = data.get("overview")

        result = {
            "poster_url": f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None,
            "overview": overview if overview else None,
        }

        cache[key] = result
        _save_cache(cache)
        return result

    except Exception:
        return {"poster_url": None, "overview": None}


def enrich_row(row, streamlit_secrets=None):
    row = row.copy()
    details = get_movie_details(row.get("tmdbId"), streamlit_secrets)

    if not isinstance(details, dict):
        details = {"poster_url": None, "overview": None}

    row["poster_url"] = details.get("poster_url")
    row["overview"] = short_overview(details.get("overview"))
    return row


def search_titles(query, limit=12):
    q = query.lower().strip()

    if not q:
        return []

    matches = movies[movies["title"].str.lower().str.contains(q, regex=False)].copy()
    matches = matches.sort_values(["rating_count", "weighted_score"], ascending=False)
    return matches["title"].head(limit).tolist()


def get_movie_row(title, streamlit_secrets=None):
    matches = movies[movies["title"].str.lower() == title.lower()]

    if matches.empty:
        return None

    row = matches.iloc[0].copy()
    row = enrich_row(row, streamlit_secrets)
    return row.to_dict()


def recommend_by_title(title, top_n=12, streamlit_secrets=None):
    idx = title_to_index.get(title.lower())

    if idx is None:
        matches = search_titles(title, limit=1)
        if not matches:
            return pd.DataFrame()
        idx = title_to_index[matches[0].lower()]

    sim_scores = linear_kernel(genre_matrix[idx], genre_matrix).flatten()

    scored = movies.copy()
    scored["similarity"] = sim_scores
    scored = scored.drop(index=idx)
    scored = scored[scored["rating_count"] >= 10]

    max_ws = max(scored["weighted_score"].max(), 1)
    max_pop = max(scored["popularity_norm"].max(), 1)

    scored["rank_score"] = (
        0.55 * scored["similarity"]
        + 0.30 * (scored["weighted_score"] / max_ws)
        + 0.15 * (scored["popularity_norm"] / max_pop)
    )

    scored = scored.sort_values(
        ["rank_score", "rating_count"],
        ascending=False
    ).head(top_n).copy()

    scored = scored.apply(
        lambda row: enrich_row(row, streamlit_secrets),
        axis=1
    )

    return scored[
        [
            "title",
            "genres",
            "year",
            "rating_mean",
            "rating_count",
            "tmdbId",
            "poster_url",
            "overview",
            "similarity",
            "weighted_score",
            "rank_score",
        ]
    ]


def popular_movies(top_n=8, streamlit_secrets=None):
    scored = movies[movies["rating_count"] >= 50].sort_values(
        ["weighted_score", "rating_count"],
        ascending=False
    ).head(top_n).copy()

    scored = scored.apply(
        lambda row: enrich_row(row, streamlit_secrets),
        axis=1
    )

    return scored[
        [
            "title",
            "genres",
            "year",
            "rating_mean",
            "rating_count",
            "tmdbId",
            "poster_url",
            "overview",
            "weighted_score",
        ]
    ]
