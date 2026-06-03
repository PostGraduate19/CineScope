import sys
from pathlib import Path

# The absolute first action: force the project directory into Python's lookup path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# NOW you can safely import your project modules
import streamlit as st
import pandas as pd
import random
import requests
import uuid
import streamlit.components.v1 as components
from src.recommender import (
    search_titles,
    recommend_by_title,
    popular_movies,
    get_movie_row,
    get_api_key,
)
from src.database import init_db, log_interaction

# --- CONFIGURATION & STATE ---
st.set_page_config(page_title="CineScope", page_icon="🎬", layout="wide")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    init_db()  # Ensure SQLite database is structurally ready
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

# --- CACHED DATA FETCHING ---
@st.cache_data(show_spinner=False)
def fetch_popular_pool(limit):
    return popular_movies(limit, st.secrets)

def fetch_recommendations(title, session_id, top_n=12):
    return recommend_by_title(title, session_id=session_id, top_n=top_n, streamlit_secrets=st.secrets)

@st.cache_data(show_spinner=False)
def fetch_movie_row(title):
    return get_movie_row(title, st.secrets)

@st.cache_data(show_spinner=False)
def fetch_trailer_key(tmdb_id):
    """Lazily fetches the official YouTube trailer ID from TMDB."""
    if not tmdb_id or pd.isna(tmdb_id): return None
    api_key = get_api_key(st.secrets)
    if not api_key: return None
    
    try:
        url = f"https://api.themoviedb.org/3/movie/{int(tmdb_id)}/videos"
        r = requests.get(url, params={'api_key': api_key}, timeout=5)
        if r.status_code == 200:
            for vid in r.json().get('results', []):
                if vid.get('site') == 'YouTube' and vid.get('type') == 'Trailer':
                    return vid.get('key')
    except Exception:
        return None
    return None

@st.cache_data(show_spinner=False)
def fetch_watch_providers(tmdb_id, region="IN"):
    """Lazily fetches Indian streaming providers from TMDB."""
    if not tmdb_id or pd.isna(tmdb_id): return None
    api_key = get_api_key(st.secrets)
    if not api_key: return None
    
    try:
        url = f"https://api.themoviedb.org/3/movie/{int(tmdb_id)}/watch/providers"
        r = requests.get(url, params={'api_key': api_key}, timeout=5)
        if r.status_code == 200:
            results = r.json().get('results', {})
            if region in results:
                return results[region]
    except Exception:
        return None
    return None

# --- INITIALIZE RANDOM DAILY SELECTION ---
if st.session_state.daily_hero is None:
    pool = fetch_popular_pool(40)
    if not pool.empty:
        sampled = pool.sample(n=min(9, len(pool)))
        st.session_state.daily_hero = sampled.iloc[0].to_dict()
        st.session_state.daily_trending = sampled.iloc[1:]

# --- HELPER FUNCTIONS ---
def split_genres(genres, limit=2):
    clean = [g.strip() for g in str(genres).split("|") if g.strip() and g.strip() != "(no genres listed)"]
    return clean[:limit]

def short_text(text, limit=28):
    text = str(text or "").strip()
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "..."

def render_image(url, width=None):
    if isinstance(url, str) and url.strip():
        st.image(url, width='stretch' if not width else width)
    else:
        st.image("https://via.placeholder.com/300x450.png?text=No+Poster", width='stretch')

def update_history(movie_dict):
    if not movie_dict: return
    history = st.session_state.search_history
    history = [m for m in history if m['title'] != movie_dict['title']]
    history.insert(0, movie_dict)
    st.session_state.search_history = history[:8]

# --- DIALOG UI ---
@st.dialog("Movie Details", width="large")
def show_movie_dialog():
    movie = st.session_state.dialog_movie
    if not movie: return

    # Log explicit view details telemetry record
    log_interaction(st.session_state.session_id, movie.get("tmdbId"), movie.get("title"), "view_details")

    col1, col2 = st.columns([1, 2.5], gap="large")
    with col1:
        render_image(movie.get("poster_url"))
    with col2:
        st.header(movie["title"])
        st.caption(" • ".join(split_genres(movie.get("genres", ""), limit=5)))

        m1, m2, m3 = st.columns(3)
        m1.metric("Rating", f"⭐ {float(movie.get('rating_mean', 0)):.1f}")
        year_val = movie.get("year")
        m2.metric("Year", str(int(year_val)) if pd.notna(year_val) else "—")
        m3.metric("Votes", int(movie.get('rating_count', 0)))

        st.divider()
        
        tab_info, tab_trailer, tab_watch = st.tabs(["Overview", "Trailer", "Where to Watch"])
        
        with tab_info:
            st.write(movie.get("overview", "No summary available."))
            
        with tab_trailer:
            trailer_key = fetch_trailer_key(movie.get("tmdbId"))
            if trailer_key:
                iframe_html = f'''
                    <iframe width="100%" height="315" 
                    src="https://www.youtube-nocookie.com/embed/{trailer_key}?rel=0" 
                    title="YouTube video player" frameborder="0" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                    allowfullscreen></iframe>
                '''
                components.html(iframe_html, height=315)
            else:
                st.info("No official trailer available.")
                
        with tab_watch:
            providers = fetch_watch_providers(movie.get("tmdbId"))
            if providers and 'flatrate' in providers:
                st.write("**Available on Subscription:**")
                cols = st.columns(6)
                for idx, provider in enumerate(providers['flatrate']):
                    with cols[idx % 6]:
                        logo_url = f"https://image.tmdb.org/t/p/w92{provider['logo_path']}"
                        st.image(logo_url, caption=provider['provider_name'], width='stretch')
            else:
                st.info("No streaming subscription providers found for this title in India.")

        st.write("")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("❤️ Like Movie", width='stretch'):
                log_interaction(st.session_state.session_id, movie.get("tmdbId"), movie.get("title"), "like")
                st.toast(f"Saved {movie.get('title')} to preferences!")
        with col_btn2:
            if st.button("Close", width='stretch'):
                st.session_state.dialog_movie = None
                st.rerun()

# --- MAIN UI: HERO & SEARCH ---
st.title("🎬 CineScope")

search_col, action_col = st.columns([4, 1])
with search_col:
    query = st.text_input("Find a movie", placeholder="Type a movie title...", label_visibility="collapsed")
    selected = None
    if query:
        matches = search_titles(query)
        if matches:
            selected = st.selectbox("Select match", matches, label_visibility="collapsed")
        else:
            st.warning("No matching movie found.")

with action_col:
    if st.button("Search", type="primary", width='stretch') and selected:
        # Clear out the dialog movie memory to prevent ghosts during new searches
        st.session_state.dialog_movie = None 
        st.session_state.active_search = selected
        row = fetch_movie_row(selected)
        if row: update_history(row)

# 2. Randomized Mood Suggestor
st.write("")
st.caption("🎭 **Mood Suggestor**")
moods = {
    "🔥 Action / Adrenaline": ["The Matrix", "Mad Max: Fury Road", "Die Hard", "Gladiator", "John Wick"],
    "😂 Comedy & Chill": ["Toy Story", "Superbad", "Step Brothers", "The Hangover", "Dumb and Dumber"],
    "🌑 Dark & Gritty": ["The Dark Knight", "Se7en", "Fight Club", "Prisoners", "Joker"],
    "🛸 Sci-Fi & Space": ["Star Wars: Episode IV - A New Hope", "Interstellar", "Alien", "Blade Runner 2049"],
    "❤️ Romance & Drama": ["Titanic", "The Notebook", "La La Land", "Forrest Gump", "Pride & Prejudice"]
}

mood_cols = st.columns(len(moods))
for idx, (mood_label, anchors) in enumerate(moods.items()):
    with mood_cols[idx]:
        if st.button(mood_label, width='stretch'):
            st.session_state.dialog_movie = None
            random_anchor = random.choice(anchors)
            st.session_state.active_search = random_anchor
            row = fetch_movie_row(random_anchor)
            if row: update_history(row)

st.divider()

# --- CONTENT RENDERING ---
active_target = st.session_state.active_search
hero_movie = None

if active_target:
    hero_movie = fetch_movie_row(active_target)
else:
    hero_movie = st.session_state.daily_hero

# Render Hero Movie
if hero_movie:
    st.subheader("Selected Movie" if active_target else "Featured Today")
    with st.container(border=True):
        left, right = st.columns([1, 3], gap="large")
        with left:
            render_image(hero_movie.get("poster_url"))
        with right:
            st.title(hero_movie['title'])
            st.caption(" • ".join(split_genres(hero_movie.get('genres', ''), limit=4)))
            st.write(hero_movie.get('overview', 'No summary available.')) 

            m1, m2, m3 = st.columns(3)
            m1.metric("Rating", f"⭐ {float(hero_movie.get('rating_mean', 0)):.1f}")
            year_val = hero_movie.get("year")
            m2.metric("Year", str(int(year_val)) if pd.notna(year_val) else "—")
            m3.metric("Votes", int(hero_movie.get('rating_count', 0)))

            st.write("")
            btn_col1, btn_col2 = st.columns(2)
            if btn_col1.button("▶ Watch Trailer", key="hero_watch", width='stretch', type="primary"):
                st.session_state.dialog_movie = hero_movie
                # Native call instead of rerun
                show_movie_dialog()
            if btn_col2.button("Details", key="hero_detail", width='stretch'):
                st.session_state.dialog_movie = hero_movie
                update_history(hero_movie)
                # Native call instead of rerun
                show_movie_dialog()

# --- REUSABLE CARD RENDERER ---
def render_movie_card(row, prefix, index):
    with st.container(border=True):
        render_image(row.get("poster_url"))
        st.markdown(f"**{short_text(row['title'], 22)}**")
        
        year = str(int(row.get('year'))) if pd.notna(row.get('year')) else "—"
        genres = " • ".join(split_genres(row.get('genres', '')))
        st.caption(f"{year} | {genres}")
        
        st.write(f"⭐ {float(row.get('rating_mean', 0)):.1f}")
        
        movie_id = row.get('tmdbId')
        if pd.isna(movie_id) or movie_id is None:
            movie_id = abs(hash(str(row['title'])))
            
        unique_button_key = f"btn_{prefix}_{index}_{int(movie_id)}"
        
        if st.button("Details", key=unique_button_key, width="stretch"):
            st.session_state.dialog_movie = row.to_dict() if isinstance(row, pd.Series) else row
            update_history(st.session_state.dialog_movie)
            # Native call instead of rerun
            show_movie_dialog()

# Render Recommendations Grid
if active_target:
    st.subheader(f"🔮 Handpicked For You '{active_target}'")
    recs = fetch_recommendations(active_target, st.session_state.session_id)
    
    if not recs.empty:
        cols = st.columns(4, gap="medium")
        for i, (_, row) in enumerate(recs.head(8).iterrows()):
            with cols[i % 4]:
                render_movie_card(row, "rec", i)

st.divider()

# --- DYNAMIC FOOTER: HISTORY OR POPULAR ---
if st.session_state.search_history:
    st.subheader("🐾 Your Movie Trail")
    cols = st.columns(4, gap="medium")
    for i, hist_movie in enumerate(st.session_state.search_history):
        with cols[i % 4]:
            render_movie_card(hist_movie, "hist", i)
else:
    st.subheader("🔥 Trending Movies")
    if st.session_state.daily_trending is not None:
        cols = st.columns(4, gap="medium")
        for i, (_, row) in enumerate(st.session_state.daily_trending.iterrows()):
            with cols[i % 4]:
                render_movie_card(row, "pop", i)

# NOTE: The block that used to manually force 'show_movie_dialog()' to execute 
# at the end of the script has been completely deleted.