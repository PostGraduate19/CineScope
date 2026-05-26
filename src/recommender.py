from pathlib import Path
import sqlite3
import json
import os
import pickle
import pandas as pd
import requests
import re
from rapidfuzz import fuzz
from dotenv import load_dotenv
from sklearn.metrics.pairwise import linear_kernel

load_dotenv()

BASE = Path(__file__).resolve().parents[1]
MODEL_DIR = BASE / 'models'
TMDB_API_KEY = os.getenv('TMDB_API_KEY', '')
TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w500'
TMDB_MOVIE_URL = 'https://api.themoviedb.org/3/movie/{tmdb_id}'
CACHE_FILE = MODEL_DIR / 'poster_cache.json'

# HYBRID RANKING PARAMETERS
WEIGHT_CONTENT = 0.40      # Match with the target movie
WEIGHT_PROFILE = 0.20      # Match with user's historical clicks/likes
WEIGHT_SVD = 0.25          # Matrix Factorization predictive quality
WEIGHT_POPULARITY = 0.15   # Global baseline popularity

with open(MODEL_DIR / 'movies.pkl', 'rb') as f:
    movies = pickle.load(f)

with open(MODEL_DIR / 'genre_matrix.pkl', 'rb') as f:
    genre_matrix = pickle.load(f)

with open(MODEL_DIR / 'title_to_index.json', 'r', encoding='utf-8') as f:
    title_to_index = json.load(f)

# Load the newly trained Collaborative Filtering Model
with open(MODEL_DIR / 'svd_model.pkl', 'rb') as f:
    svd_model = pickle.load(f)

DB_PATH = BASE / 'data' / 'user_interactions.db'


def _load_cache():
    if CACHE_FILE.exists():
        try:
            data = json.loads(CACHE_FILE.read_text(encoding='utf-8'))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def _save_cache(cache):
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding='utf-8')


def get_api_key(streamlit_secrets=None):
    if TMDB_API_KEY:
        return TMDB_API_KEY
    if streamlit_secrets:
        try:
            return streamlit_secrets['TMDB_API_KEY']
        except Exception:
            return ''
    return ''


def short_overview(text, limit=150):
    if not text:
        return 'No summary available.'
    text = ' '.join(str(text).split())
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(' ', 1)[0] + '...'


def get_movie_details(tmdb_id, streamlit_secrets=None):
    api_key = get_api_key(streamlit_secrets)

    if not api_key or pd.isna(tmdb_id):
        return {'poster_url': None, 'overview': None}

    cache = _load_cache()
    key = str(int(tmdb_id))
    cached = cache.get(key)

    if isinstance(cached, dict):
        return {
            'poster_url': cached.get('poster_url'),
            'overview': cached.get('overview'),
        }

    try:
        url = TMDB_MOVIE_URL.format(tmdb_id=int(tmdb_id))
        r = requests.get(url, params={'api_key': api_key}, timeout=10)

        if r.status_code != 200:
            result = {'poster_url': None, 'overview': None}
            cache[key] = result
            _save_cache(cache)
            return result

        data = r.json()
        poster_path = data.get('poster_path')
        overview = data.get('overview')

        result = {
            'poster_url': f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None,
            'overview': overview if overview else None,
        }

        cache[key] = result
        _save_cache(cache)
        return result

    except Exception:
        return {'poster_url': None, 'overview': None}


def enrich_row(row, streamlit_secrets=None):
    row = row.copy()
    details = get_movie_details(row.get('tmdbId'), streamlit_secrets)

    if not isinstance(details, dict):
        details = {'poster_url': None, 'overview': None}

    row['poster_url'] = details.get('poster_url')
    # Fetch the full text directly from the API without truncation
    row['overview'] = details.get('overview') if details.get('overview') else 'No summary available.'
    return row

def search_titles(query, limit=12):
    q = query.lower().strip()
    if not q:
        return []

    # Normalize the query by removing all non-alphanumeric characters
    q_norm = re.sub(r'[^a-z0-9]', '', q)

    # Normalize the dataset titles in the exact same way for comparison
    normalized_titles = movies['title'].str.lower().str.replace(r'[^a-z0-9]', '', regex=True)

    # Match the normalized strings, but return the original formatted titles
    matches = movies[normalized_titles.str.contains(q_norm, regex=False)].copy()
    
    matches = matches.sort_values(['rating_count', 'weighted_score'], ascending=False)
    return matches['title'].head(limit).tolist()

def get_movie_row(title, streamlit_secrets=None):
    matches = movies[movies['title'].str.lower() == title.lower()]
    if matches.empty:
        return None

    row = matches.iloc[0].copy()
    row = enrich_row(row, streamlit_secrets)
    return row.to_dict()


def recommend_by_title(title, session_id=None, top_n=12, streamlit_secrets=None):
    idx = title_to_index.get(title.lower())
    if idx is None:
        matches = search_titles(title, limit=1)
        if not matches: return pd.DataFrame()
        idx = title_to_index[matches[0].lower()]

    scored = movies.copy()

    # 1. Base Content Similarity (Target Movie)
    scored['similarity'] = linear_kernel(genre_matrix[idx], genre_matrix).flatten()

    # 2. User Profile Similarity (Historical Data from SQLite)
    profile_sims = []
    if session_id and DB_PATH.exists():
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT tmdb_id, interaction_type FROM interactions WHERE session_id = ?", (session_id,))
            history = c.fetchall()
            conn.close()

            for tmdb_id, i_type in history:
                hist_matches = scored[scored['tmdbId'] == tmdb_id].index
                if not hist_matches.empty:
                    # Weigh explicit 'likes' 5x heavier than implicit 'views'
                    weight = 1.0 if i_type == 'like' else 0.2
                    sim = linear_kernel(genre_matrix[hist_matches[0]], genre_matrix).flatten() * weight
                    profile_sims.append(sim)
        except Exception:
            pass

    if profile_sims:
        scored['profile_similarity'] = sum(profile_sims) / len(profile_sims)
    else:
        scored['profile_similarity'] = 0.0

    # 3. Collaborative Filtering Predictive Score (SVD)
    # SVD predicts rating on a 0.5 - 5.0 scale. We normalize it to 0.0 - 1.0.
    def get_svd_score(movie_id):
        try:
            return (svd_model.predict(uid=session_id, iid=movie_id).est - 0.5) / 4.5
        except Exception:
            return 0.5

    scored['svd_score'] = scored['movieId'].apply(get_svd_score)

    # 4. Apply Filters and Modifiers
    scored = scored.drop(index=idx)
    scored = scored[scored['rating_count'] >= 10]

    max_pop = max(scored['popularity_norm'].max(), 1)
    target_title = movies.loc[idx, 'title']
    target_base = re.sub(r'\(\d{4}\)', '', target_title).strip().lower()
    target_year = movies.loc[idx, 'year']

    def calculate_modifiers(row):
        cand_base = re.sub(r'\(\d{4}\)', '', str(row['title'])).strip().lower()
        match_ratio = fuzz.partial_ratio(target_base, cand_base)
        title_boost = 1.0 + ((match_ratio - 85) / 15) if match_ratio >= 85 else 1.0

        cand_year = row['year']
        if pd.isna(target_year) or pd.isna(cand_year):
            time_penalty = 1.0
        else:
            age_diff = abs(target_year - cand_year)
            time_penalty = max(0.60, 1.0 - (age_diff * 0.02))

        return title_boost * time_penalty

    scored['modifiers'] = scored.apply(calculate_modifiers, axis=1)

    # 5. The Multi-Variate Hybrid Engine
    scored['rank_score'] = (
        (WEIGHT_CONTENT * scored['similarity'])
        + (WEIGHT_PROFILE * scored['profile_similarity'])
        + (WEIGHT_SVD * scored['svd_score'])
        + (WEIGHT_POPULARITY * (scored['popularity_norm'] / max_pop))
    ) * scored['modifiers']

    scored = scored.sort_values(['rank_score', 'rating_count'], ascending=False).head(top_n).copy()
    scored = scored.apply(lambda row: enrich_row(row, streamlit_secrets), axis=1)

    return scored[[
        'title', 'genres', 'year', 'rating_mean', 'rating_count', 'tmdbId',
        'poster_url', 'overview', 'similarity', 'weighted_score', 'rank_score'
    ]]


def popular_movies(top_n=8, streamlit_secrets=None):
    scored = movies[movies['rating_count'] >= 50].sort_values(
        ['weighted_score', 'rating_count'], ascending=False
    ).head(top_n).copy()

    scored = scored.apply(lambda row: enrich_row(row, streamlit_secrets), axis=1)

    return scored[[
        'title', 'genres', 'year', 'rating_mean', 'rating_count', 'tmdbId',
        'poster_url', 'overview', 'weighted_score'
    ]]
