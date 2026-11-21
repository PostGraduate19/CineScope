import sys
from pathlib import Path
import random
import urllib.parse
import uuid

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

# Ensure the project root is on sys.path before importing local modules
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database import init_db, log_interaction
from src.recommender import (
    get_api_key,
    get_movie_row,
    popular_movies,
    recommend_by_title,
    search_titles,
)

# --- CONFIGURATION & STATE ---
st.set_page_config(page_title="CineScope", page_icon="🎬", layout="wide")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    init_db()
if "dialog_movie" not in st.session_state:
    st.session_state.dialog_movie = None
if "search_history" not in st.session_state:
    st.session_state.search_history = []
if "active_search" not in st.session_state:
    st.session_state.active_search = None
if "daily_hero" not in st.session_state:
    st.session_state.daily_hero = None
if "daily_trending" not in st.session_state:
    st.session_state.daily_trending = None

PLACEHOLDER_POSTER = "https://via.placeholder.com/300x450.png?text=No+Poster"


# --- SAFE DATA & API HELPERS ---
def fetch_popular_pool(limit: int) -> pd.DataFrame:
    try:
        df = popular_movies(limit, st.secrets)
        return df if isinstance(df, pd.DataFrame) else pd.DataFrame()
    except Exception as exc:
        st.error(f"Failed to load popular movies pool: {exc}")
        return pd.DataFrame()


def fetch_recommendations(title: str, session_id: str, top_n: int = 12) -> pd.DataFrame:
    try:
        df = recommend_by_title(
            title,
            session_id=session_id,
            top_n=top_n,
            streamlit_secrets=st.secrets,
        )
        return df if isinstance(df, pd.DataFrame) else pd.DataFrame()
    except Exception as exc:
        st.error(f"Failed to generate recommendations for '{title}': {exc}")
        return pd.DataFrame()


def fetch_movie_row(title: str):
    try:
        return get_movie_row(title, st.secrets)
    except Exception as exc:
        st.error(f"Failed to load metadata for '{title}': {exc}")
        return None


@st.cache_data(show_spinner=False)
def fetch_trailer_key(tmdb_id, api_key: str):
    """Lazily fetches the official YouTube trailer ID from TMDB."""
    if not tmdb_id or pd.isna(tmdb_id) or not api_key:
        return None
    try:
        url = f"https://api.themoviedb.org/3/movie/{int(tmdb_id)}/videos"
        resp = requests.get(url, params={"api_key": api_key}, timeout=5)
        if resp.status_code == 200:
            for vid in resp.json().get("results", []):
                if vid.get("site") == "YouTube" and vid.get("type") == "Trailer":
                    return vid.get("key")
    except Exception:
        return None
    return None


@st.cache_data(show_spinner=False)
def fetch_watch_providers(tmdb_id, api_key: str, region: str = "IN"):
    """Lazily fetches streaming providers from TMDB for the target region."""
    if not tmdb_id or pd.isna(tmdb_id) or not api_key:
        return None
    try:
        url = f"https://api.themoviedb.org/3/movie/{int(tmdb_id)}/watch/providers"
        resp = requests.get(url, params={"api_key": api_key}, timeout=5)
        if resp.status_code == 200:
            results = resp.json().get("results", {})
            return results.get(region)
    except Exception:
        return None
    return None


# --- INITIALIZE DAILY HERO & TRENDING ---
if st.session_state.daily_hero is None or st.session_state.daily_trending is None:
    pool = fetch_popular_pool(40)
    if not pool.empty:
        sampled = pool.sample(n=min(9, len(pool)), random_state=42)
        st.session_state.daily_hero = sampled.iloc[0].to_dict()
        st.session_state.daily_trending = sampled.iloc[1:]


# --- FORMATTING & STATE HELPERS ---
def split_genres(genres, limit: int = 2) -> list[str]:
    clean = [
        g.strip()
        for g in str(genres).split("|")
        if g.strip() and g.strip() != "(no genres listed)"
    ]
    return clean[:limit]


def short_text(text, limit: int = 28) -> str:
    cleaned = str(text or "").strip()
    if len(cleaned) <= limit:
        return cleaned
    trimmed = cleaned[:limit].rsplit(" ", 1)[0]
    return f"{trimmed}..."


def render_image(url, width=None):
    target = url.strip() if isinstance(url, str) and url.strip() else PLACEHOLDER_POSTER
    if isinstance(width, int):
        st.image(target, width=width)
    else:
        st.image(target, use_container_width=True)


def update_history(movie_dict):
    if not movie_dict or "title" not in movie_dict:
        return
    history = [m for m in st.session_state.search_history if m.get("title") != movie_dict["title"]]
    history.insert(0, movie_dict)
    st.session_state.search_history = history[:8]


def safe_int(val, default: int = 0) -> int:
    try:
        if pd.isna(val):
            return default
        return int(float(val))
    except (ValueError, TypeError):
        return default


def safe_float(val, default: float = 0.0) -> float:
    try:
        if pd.isna(val):
            return default
        return float(val)
    except (ValueError, TypeError):
        return default


# --- MOVIE DETAILS DIALOG ---
@st.dialog("Movie Details", width="large")
def show_movie_dialog():
    movie = st.session_state.dialog_movie
    if not movie:
        return

    log_interaction(
        st.session_state.session_id,
        movie.get("tmdbId"),
        movie.get("title"),
        "view_details",
    )

    api_key = get_api_key(st.secrets)
    col1, col2 = st.columns([1, 2.5], gap="large")

    with col1:
        render_image(movie.get("poster_url"))

    with col2:
        st.header(movie.get("title", "Unknown Title"))
        st.caption(" • ".join(split_genres(movie.get("genres", ""), limit=5)))

        m1, m2, m3 = st.columns(3)
        m1.metric("Rating", f"⭐ {safe_float(movie.get('rating_mean')):.1f}")
        year_val = movie.get("year")
        m2.metric("Year", str(safe_int(year_val)) if pd.notna(year_val) else "—")
        m3.metric("Votes", safe_int(movie.get("rating_count")))

        st.divider()

        tab_info, tab_trailer, tab_watch = st.tabs(["Overview", "Trailer", "Where to Watch"])

        with tab_info:
            st.write(movie.get("overview") or "No summary available.")

        with tab_trailer:
            trailer_key = fetch_trailer_key(movie.get("tmdbId"), api_key)
            if trailer_key:
                iframe_html = f"""
                    <iframe width="100%" height="315"
                    src="https://www.youtube-nocookie.com/embed/{trailer_key}?rel=0"
                    title="YouTube video player" frameborder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                    allowfullscreen></iframe>
                """
                components.html(iframe_html, height=315)
            else:
                st.info("No official trailer available.")

        with tab_watch:
            providers = fetch_watch_providers(movie.get("tmdbId"), api_key, region="IN")
            if providers and providers.get("flatrate"):
                st.write("**Available on Subscription:**")
                cols = st.columns(6)
                for idx, provider in enumerate(providers["flatrate"]):
                    with cols[idx % 6]:
                        logo_path = provider.get("logo_path", "")
                        logo_url = f"https://image.tmdb.org/t/p/w92{logo_path}" if logo_path else PLACEHOLDER_POSTER
                        st.image(logo_url, caption=provider.get("provider_name", ""), use_container_width=True)
            else:
                st.info("No streaming subscription providers found for this title in India.")

        st.write("")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("❤️ Like Movie", use_container_width=True):
                log_interaction(
                    st.session_state.session_id,
                    movie.get("tmdbId"),
                    movie.get("title"),
                    "like",
                )
                st.toast(f"Saved {movie.get('title')} to preferences!")
        with col_btn2:
            if st.button("Close", use_container_width=True):
                st.session_state.dialog_movie = None
                st.rerun()


# --- MAIN UI: SEARCH & MOOD SUGGESTOR ---
st.title("🎬 CineScope")

search_col, action_col = st.columns([4, 1])
selected = None

with search_col:
    query = st.text_input(
        "Find a movie",
        placeholder="Type a movie title...",
        label_visibility="collapsed",
    )
    if query:
        try:
            matches = search_titles(query)
        except Exception as exc:
            matches = []
            st.error(f"Search failed: {exc}")

        if matches:
            selected = st.selectbox("Select match", matches, label_visibility="collapsed")
        else:
            st.warning("No matching movie found.")

with action_col:
    if st.button("Search", type="primary", use_container_width=True) and selected:
        st.session_state.dialog_movie = None
        st.session_state.active_search = selected
        row = fetch_movie_row(selected)
        if row:
            update_history(row)

st.write("")
st.caption("🎭 **Mood Suggestor**")
moods = {
    "🔥 Action / Adrenaline": ["The Matrix", "Mad Max: Fury Road", "Die Hard", "Gladiator", "John Wick"],
    "😂 Comedy & Chill": ["Toy Story", "Superbad", "Step Brothers", "The Hangover", "Dumb and Dumber"],
    "🌑 Dark & Gritty": ["The Dark Knight", "Se7en", "Fight Club", "Prisoners", "Joker"],
    "🛸 Sci-Fi & Space": ["Star Wars: Episode IV - A New Hope", "Interstellar", "Alien", "Blade Runner 2049"],
    "❤️ Romance & Drama": ["Titanic", "The Notebook", "La La Land", "Forrest Gump", "Pride & Prejudice"],
}

mood_cols = st.columns(len(moods))
for idx, (mood_label, anchors) in enumerate(moods.items()):
    with mood_cols[idx]:
        if st.button(mood_label, key=f"mood_{idx}", use_container_width=True):
            st.session_state.dialog_movie = None
            random_anchor = random.choice(anchors)
            st.session_state.active_search = random_anchor
            row = fetch_movie_row(random_anchor)
            if row:
                update_history(row)

st.divider()

# --- HERO MOVIE SECTION ---
hero_movie = (
    fetch_movie_row(st.session_state.active_search)
    if st.session_state.active_search
    else st.session_state.daily_hero
)

if hero_movie:
    st.subheader("Selected Movie" if st.session_state.active_search else "Featured Today")
    with st.container(border=True):
        left, right = st.columns([1, 3], gap="large")
        with left:
            render_image(hero_movie.get("poster_url"))
        with right:
            st.title(hero_movie.get("title", "Unknown Title"))
            st.caption(" • ".join(split_genres(hero_movie.get("genres", ""), limit=4)))
            st.write(hero_movie.get("overview") or "No summary available.")

            m1, m2, m3 = st.columns(3)
            m1.metric("Rating", f"⭐ {safe_float(hero_movie.get('rating_mean')):.1f}")
            year_val = hero_movie.get("year")
            m2.metric("Year", str(safe_int(year_val)) if pd.notna(year_val) else "—")
            m3.metric("Votes", safe_int(hero_movie.get("rating_count")))

            st.write("")
            btn_col1, btn_col2 = st.columns(2)
            safe_query = urllib.parse.quote_plus(f"{hero_movie.get('title', '')} official trailer")
            trailer_url = f"https://www.youtube.com/results?search_query={safe_query}"

            btn_col1.link_button("▶ Watch Trailer", trailer_url, use_container_width=True)
            if btn_col2.button("Details", key="hero_detail", use_container_width=True):
                st.session_state.dialog_movie = hero_movie
                update_history(hero_movie)
                show_movie_dialog()


# --- REUSABLE MOVIE CARD ---
def render_movie_card(row, prefix: str, index: int):
    row_dict = row.to_dict() if isinstance(row, pd.Series) else dict(row)
    with st.container(border=True):
        render_image(row_dict.get("poster_url"))
        st.markdown(f"**{short_text(row_dict.get('title', 'Untitled'), 22)}**")

        year_val = row_dict.get("year")
        year_str = str(safe_int(year_val)) if pd.notna(year_val) else "—"
        genres_str = " • ".join(split_genres(row_dict.get("genres", "")))
        st.caption(f"{year_str} | {genres_str}")

        st.write(f"⭐ {safe_float(row_dict.get('rating_mean')):.1f}")

        raw_id = row_dict.get("tmdbId")
        movie_id = safe_int(raw_id) if pd.notna(raw_id) and raw_id is not None else abs(hash(str(row_dict.get("title", index))))

        safe_query = urllib.parse.quote_plus(f"{row_dict.get('title', '')} official trailer")
        trailer_url = f"https://www.youtube.com/results?search_query={safe_query}"
        st.link_button("▶ Trailer", trailer_url, use_container_width=True)

        unique_button_key = f"btn_{prefix}_{index}_{movie_id}"
        if st.button("Details", key=unique_button_key, use_container_width=True):
            st.session_state.dialog_movie = row_dict
            update_history(row_dict)
            show_movie_dialog()


# --- RECOMMENDATIONS GRID ---
if st.session_state.active_search:
    st.subheader(f"🔮 Handpicked For You '{st.session_state.active_search}'")
    recs = fetch_recommendations(st.session_state.active_search, st.session_state.session_id)

    if not recs.empty:
        cols = st.columns(4, gap="medium")
        for i, (_, row) in enumerate(recs.head(8).iterrows()):
            with cols[i % 4]:
                render_movie_card(row, "rec", i)

st.divider()

# --- HISTORY OR TRENDING FOOTER ---
if st.session_state.search_history:
    st.subheader("🐾 Your Movie Trail")
    cols = st.columns(4, gap="medium")
    for i, hist_movie in enumerate(st.session_state.search_history):
        with cols[i % 4]:
            render_movie_card(hist_movie, "hist", i)
elif st.session_state.daily_trending is not None and not st.session_state.daily_trending.empty:
    st.subheader("🔥 Trending Movies")
    cols = st.columns(4, gap="medium")
    for i, (_, row) in enumerate(st.session_state.daily_trending.iterrows()):
        with cols[i % 4]:
            render_movie_card(row, "pop", i)