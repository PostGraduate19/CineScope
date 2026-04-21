from pathlib import Path
import io
import json
import pickle
import re
import zipfile
import requests
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

BASE = Path(__file__).resolve().parents[1]
DATA_DIR = BASE / 'data'
MODEL_DIR = BASE / 'models'
DATASET_DIR = DATA_DIR / 'ml-latest-small'
URL = 'https://files.grouplens.org/datasets/movielens/ml-latest-small.zip'


def download_dataset():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if DATASET_DIR.exists() and (DATASET_DIR / 'movies.csv').exists():
        return
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        zf.extractall(DATA_DIR)


def extract_year(title: str):
    m = re.search(r'\((\d{4})\)$', str(title))
    return int(m.group(1)) if m else None


def build_artifacts():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    movies = pd.read_csv(DATASET_DIR / 'movies.csv')
    ratings = pd.read_csv(DATASET_DIR / 'ratings.csv')
    links = pd.read_csv(DATASET_DIR / 'links.csv')

    stats = ratings.groupby('movieId').agg(
        rating_count=('rating', 'count'),
        rating_mean=('rating', 'mean')
    ).reset_index()

    movies = movies.merge(stats, on='movieId', how='left')
    movies = movies.merge(links[['movieId', 'tmdbId']], on='movieId', how='left')

    movies['rating_count'] = movies['rating_count'].fillna(0)
    movies['rating_mean'] = movies['rating_mean'].fillna(0)
    movies['year'] = movies['title'].apply(extract_year)

    global_mean = ratings['rating'].mean()
    min_votes = 20
    v = movies['rating_count']
    r = movies['rating_mean']
    c = global_mean

    movies['weighted_score'] = (v / (v + min_votes) * r) + (min_votes / (v + min_votes) * c)
    movies['popularity_norm'] = movies['rating_count'] / max(movies['rating_count'].max(), 1)

    movies['genres_clean'] = (
        movies['genres']
        .fillna('')
        .replace('(no genres listed)', '', regex=False)
        .str.replace('|', ' ', regex=False)
    )

    tfidf = TfidfVectorizer(stop_words='english')
    genre_matrix = tfidf.fit_transform(movies['genres_clean'])

    with open(MODEL_DIR / 'movies.pkl', 'wb') as f:
        pickle.dump(movies, f)

    with open(MODEL_DIR / 'genre_matrix.pkl', 'wb') as f:
        pickle.dump(genre_matrix, f)

    with open(MODEL_DIR / 'title_to_index.json', 'w', encoding='utf-8') as f:
        json.dump({title.lower(): idx for idx, title in enumerate(movies['title'].tolist())}, f)

    cache_file = MODEL_DIR / 'poster_cache.json'
    if not cache_file.exists():
        cache_file.write_text('{}', encoding='utf-8')


if __name__ == '__main__':
    download_dataset()
    build_artifacts()
    print('Artifacts built successfully.')
