import streamlit as st
from src.recommender import (
    search_titles,
    recommend_by_title,
    popular_movies,
    get_movie_row,
    get_api_key,
)

st.set_page_config(page_title="CineScope Fresh", page_icon="🎬", layout="wide")

if "dialog_movie" not in st.session_state:
    st.session_state.dialog_movie = None
if "last_selected" not in st.session_state:
    st.session_state.last_selected = None
if "last_results" not in st.session_state:
    st.session_state.last_results = None

st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: Inter, system-ui, sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at top left, rgba(90, 34, 139, 0.16), transparent 24%),
        radial-gradient(circle at bottom right, rgba(70, 20, 120, 0.10), transparent 22%),
        linear-gradient(180deg, #181a1f 0%, #16171c 100%);
    color: #f4f4f6;
}

.block-container {
    max-width: 1280px;
    padding-top: 1rem;
    padding-bottom: 2rem;
}

[data-testid="stSidebar"] {
    background: #14161a;
    border-right: 1px solid #262930;
}

.search-panel {
    background: linear-gradient(180deg, rgba(33, 36, 43, 0.98), rgba(24, 26, 31, 0.98));
    border: 1px solid #2d3138;
    border-radius: 22px;
    padding: 1.1rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.18);
}

.feature-card {
    background: linear-gradient(180deg, rgba(34, 37, 45, 0.96), rgba(24, 26, 31, 0.96));
    border: 1px solid #2b3038;
    border-radius: 24px;
    padding: 1.25rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 14px 30px rgba(0, 0, 0, 0.18);
}

.poster-frame img {
    border-radius: 18px;
    object-fit: cover;
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.24);
}

.hero-title {
    font-size: 2.15rem;
    font-weight: 800;
    line-height: 1.08;
    margin-bottom: 0.55rem;
    color: #f0f3ff;
    letter-spacing: -0.03em;
}

.hero-summary {
    color: #bcc4d6;
    font-size: 1rem;
    line-height: 1.6;
    margin-bottom: 1rem;
    max-width: 68ch;
}

.genre-pill-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 0.7rem 0 1rem 0;
}

.genre-pill {
    display: inline-block;
    padding: 0.38rem 0.7rem;
    border-radius: 999px;
    background: rgba(208, 175, 17, 0.12);
    border: 1px solid rgba(208, 175, 17, 0.28);
    color: #f0d76a;
    font-size: 0.82rem;
    font-weight: 600;
}

.metric-box {
    background: #1d2127;
    border: 1px solid #2f343c;
    border-radius: 16px;
    padding: 0.9rem;
    text-align: left;
}

.metric-label {
    font-size: 0.78rem;
    color: #97a0af;
    margin-bottom: 0.25rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.metric-value {
    font-size: 1.05rem;
    font-weight: 700;
    color: #f3f5fb;
}

.section-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 1.1rem 0 0.9rem 0;
}

.section-head h2 {
    margin: 0;
    font-size: 1.85rem;
    font-weight: 800;
    color: #dbe5ff;
    letter-spacing: -0.03em;
}

.movie-card {
    background: linear-gradient(180deg, rgba(30, 33, 40, 0.98), rgba(23, 25, 30, 0.98));
    border: 1px solid #2b3038;
    border-radius: 20px;
    padding: 0.85rem;
    height: 100%;
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.14);
}

.movie-card img {
    border-radius: 14px;
    aspect-ratio: 2 / 3;
    object-fit: cover;
}

.poster-title {
    margin-top: 0.75rem;
    font-size: 1rem;
    line-height: 1.28;
    color: #edf1fa;
    font-weight: 700;
    min-height: 3.1rem;
}

.poster-subtitle {
    color: #a7afbd;
    font-size: 0.88rem;
    line-height: 1.45;
    margin-top: 0.32rem;
    min-height: 4rem;
}

.rating-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    margin-top: 0.7rem;
    padding: 0.34rem 0.7rem;
    border-radius: 999px;
    background: rgba(208, 175, 17, 0.14);
    border: 1px solid rgba(208, 175, 17, 0.32);
    color: #f2d86d;
    font-size: 0.82rem;
    font-weight: 700;
}

.stTextInput > div > div > input,
.stSelectbox > div > div,
.stSelectbox [data-baseweb="select"] > div {
    background: #262b32 !important;
    border-radius: 12px !important;
}

.stButton > button {
    background: #d0af11;
    color: #161616;
    border: none;
    border-radius: 12px;
    padding: 0.65rem 1rem;
    font-weight: 700;
}

.detail-btn button {
    background: #262b32 !important;
    color: #f0f2f7 !important;
    border: 1px solid #39404a !important;
}

.dialog-close-fix button {
    margin-top: 1rem;
}

hr {
    border: none;
    border-top: 1px solid #2a2f37;
    margin: 1.2rem 0;
}
</style>
""", unsafe_allow_html=True)


def split_genres(genres):
    return [
        g.strip() for g in str(genres).split("|")
        if g.strip() and g.strip() != "(no genres listed)"
    ]


def short_text(text, limit=88):
    text = str(text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "..."


def render_genres(genres, limit=3):
    items = split_genres(genres)[:limit]
    if not items:
        return ""
    return "".join([f"<span class='genre-pill'>{g}</span>" for g in items])


def open_dialog(movie_dict):
    st.session_state.dialog_movie = movie_dict


def close_dialog():
    st.session_state.dialog_movie = None


@st.dialog("Movie details", width="large")
def show_movie_dialog():
    movie = st.session_state.dialog_movie
    if movie is None:
        return

    left, right = st.columns([0.72, 1.28], gap="large", vertical_alignment="top")

    with left:
        st.markdown('<div class="poster-frame">', unsafe_allow_html=True)
        if movie.get("poster_url"):
            st.image(movie["poster_url"], width=280)
        else:
            st.info("Poster not available")
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.subheader(movie["title"])
        st.markdown(f"<div class='genre-pill-row'>{render_genres(movie.get('genres', ''), 4)}</div>", unsafe_allow_html=True)

        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(
                f"<div class='metric-box'><div class='metric-label'>Rating</div><div class='metric-value'>⭐ {float(movie['rating_mean']):.2f}</div></div>",
                unsafe_allow_html=True
            )
        with m2:
            year_val = movie.get("year")
            year_text = str(int(year_val)) if year_val else "—"
            st.markdown(
                f"<div class='metric-box'><div class='metric-label'>Year</div><div class='metric-value'>{year_text}</div></div>",
                unsafe_allow_html=True
            )
        with m3:
            st.markdown(
                f"<div class='metric-box'><div class='metric-label'>Votes</div><div class='metric-value'>{int(movie['rating_count'])}</div></div>",
                unsafe_allow_html=True
            )

        st.markdown("<hr>", unsafe_allow_html=True)
        st.write(movie.get("overview", "No summary available."))

        if movie.get("rank_score") is not None:
            st.caption(f"Recommendation score: {float(movie['rank_score']):.3f}")

        st.markdown('<div class="dialog-close-fix">', unsafe_allow_html=True)
        if st.button("Close", key="dialog_close_btn", use_container_width=True):
            close_dialog()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


api_key = get_api_key(st.secrets)

with st.sidebar:
    st.markdown("## 🎬")
    st.write("🏠")
    st.write("🔎")
    st.write("🎞️")
    st.write("📺")
    st.write("⭐")
    st.write("⚙️")

st.markdown('<div class="search-panel">', unsafe_allow_html=True)
query = st.text_input("Search movie title", placeholder="Search for a movie")
selected = None

if query:
    matches = search_titles(query)
    if matches:
        selected = st.selectbox("Pick a title", matches, key="movie_selector")
    else:
        st.info("No matching movie found.")

recommend = st.button("Get recommendations")
st.markdown("</div>", unsafe_allow_html=True)

if recommend and selected:
    st.session_state.last_selected = selected
    with st.spinner("Loading movie details and recommendations...", show_time=True):
        st.session_state.last_results = recommend_by_title(
            selected,
            top_n=12,
            streamlit_secrets=st.secrets,
        )

hero_movie = None
if st.session_state.last_selected:
    row = get_movie_row(st.session_state.last_selected, st.secrets)
    if row is not None:
        hero_movie = row
else:
    popular = popular_movies(1, st.secrets)
    if len(popular) > 0:
        hero_movie = popular.iloc[0].to_dict()

if hero_movie is not None:
    st.markdown('<div class="section-head"><h2>Selected movie</h2></div>', unsafe_allow_html=True)
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)

    left, right = st.columns([0.9, 2.1], gap="large", vertical_alignment="top")

    with left:
        st.markdown('<div class="poster-frame">', unsafe_allow_html=True)
        if hero_movie.get("poster_url"):
            st.image(hero_movie["poster_url"], width=290)
        else:
            st.info("Poster not available")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown(f"<div class='hero-title'>{hero_movie['title']}</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='hero-summary'>{hero_movie.get('overview', 'No summary available.')}</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div class='genre-pill-row'>{render_genres(hero_movie.get('genres', ''), 4)}</div>",
            unsafe_allow_html=True
        )

        mx1, mx2, mx3 = st.columns(3)
        with mx1:
            st.markdown(
                f"<div class='metric-box'><div class='metric-label'>Rating</div><div class='metric-value'>⭐ {float(hero_movie['rating_mean']):.2f}</div></div>",
                unsafe_allow_html=True
            )
        with mx2:
            year_val = hero_movie.get("year")
            year_text = str(int(year_val)) if year_val else "—"
            st.markdown(
                f"<div class='metric-box'><div class='metric-label'>Year</div><div class='metric-value'>{year_text}</div></div>",
                unsafe_allow_html=True
            )
        with mx3:
            st.markdown(
                f"<div class='metric-box'><div class='metric-label'>Votes</div><div class='metric-value'>{int(hero_movie['rating_count'])}</div></div>",
                unsafe_allow_html=True
            )

        a1, a2 = st.columns([1, 1])
        with a1:
            st.button("▶ Watch style", key="hero_watch_btn", use_container_width=True)
        with a2:
            if st.button("Details", key="hero_detail_btn", use_container_width=True):
                open_dialog(hero_movie)
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.last_results is not None and len(st.session_state.last_results) > 0:
    st.markdown('<div class="section-head"><h2>Recommendations</h2></div>', unsafe_allow_html=True)
    recs = st.session_state.last_results
    cols = st.columns(6, gap="medium")

    for i, (_, row) in enumerate(recs.head(6).iterrows()):
        with cols[i]:
            st.markdown('<div class="movie-card">', unsafe_allow_html=True)

            if row.get("poster_url"):
                st.image(row["poster_url"], use_container_width=True)
            else:
                st.info("No poster")

            st.markdown(f"<div class='poster-title'>{row['title']}</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='poster-subtitle'>{short_text(row.get('overview', 'No summary available.'), 80)}</div>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<div class='rating-pill'>⭐ {float(row['rating_mean']):.2f}</div>",
                unsafe_allow_html=True
            )

            st.markdown('<div class="detail-btn">', unsafe_allow_html=True)
            if st.button("Details", key=f"rec_detail_{i}", use_container_width=True):
                open_dialog(row.to_dict())
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

popular_row = popular_movies(6, st.secrets)
if len(popular_row) > 0:
    st.markdown('<div class="section-head"><h2>Continue with your Movies</h2></div>', unsafe_allow_html=True)
    cols2 = st.columns(6, gap="medium")

    for i, (_, row) in enumerate(popular_row.iterrows()):
        with cols2[i]:
            st.markdown('<div class="movie-card">', unsafe_allow_html=True)

            if row.get("poster_url"):
                st.image(row["poster_url"], use_container_width=True)
            else:
                st.info("No poster")

            st.markdown(f"<div class='poster-title'>{row['title']}</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='poster-subtitle'>{short_text(row.get('overview', 'No summary available.'), 80)}</div>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<div class='rating-pill'>⭐ {float(row['rating_mean']):.2f}</div>",
                unsafe_allow_html=True
            )

            st.markdown('<div class="detail-btn">', unsafe_allow_html=True)
            if st.button("Details", key=f"popular_detail_{i}", use_container_width=True):
                open_dialog(row.to_dict())
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.dialog_movie is not None:
    show_movie_dialog()
