# 🎬 CineScope: Hybrid Personalized Recommender Engine

CineScope is a next-generation, state-aware movie recommendation platform. Moving beyond rigid keyword matching, the system utilizes a high-performance **Multi-Variate Hybrid Recommendation Architecture** that unifies deep content semantics with user behavioral modeling and predictive matrix factorization.

---🚀 **Live Deployment:** [Explore CineScope on Streamlit Community Cloud](https://share.streamlit.io/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME/main/app.py)  
📂 **Source Code:** [GitHub Repository](https://github.com/PostGraduate19/CineScope)

## 🚀 Key Architectural Upgrades

Compared to standard item-to-item matching systems, CineScope introduces production-grade data pipelines:

* **Predictive Matrix Factorization (SVD):** Implements Singular Value Decomposition via `scikit-surprise` trained on user-item interaction matrices to uncover latent behavioral features and project user preferences mathematically.
* **Real-Time Telemetry Tracking:** Powered by a local SQLite pipeline that non-blockingly captures both implicit behavior (`view_details`) and explicit signals (`like`) during live sessions.
* **Dynamic Multi-Variate Scoring:** Merges multiple core metrics into a singular ranking score dynamically weighted across:
    * *Target Content Similarity* (TF-IDF Cosine Distance)
    * *Live User Profile Affinity* (Historical Clicks/Likes)
    * *Collaborative Filtering Baseline* (SVD Prediction)
    * *Global Popularity Normalization*
* **Modern Tabbed UI & Zero-Cookie Streams:** A fully decoupled layout utilizing Streamlit's structural tab components, integration with regional OTT availability APIs (Geo-locked to India streaming providers), and secure YouTube embed delivery systems via privacy-enhanced domains (`youtube-nocookie.com`).

---

## 🛠️ Tech Stack & Core Math

* **Frontend UI:** Streamlit Engine (v1.35+)
* **Machine Learning / Math Math:** Scikit-learn, Scikit-surprise (Cython Optimized SVD)
* **Data Pipeline:** Pandas, NumPy
* **Database Infrastructure:** SQLite3
* **Metadata Integration:** TMDB (The Movie Database) API

---

## 📦 Local Installation & Setup

### 1. Environment Cloning & System Prerequisites
Because the collaborative filtering layer leverages C-extensions, specialized build tools must be staged chronologically. Open your terminal in the root project folder:

```bash
# Initialize clean virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install strictly isolated pinning tools first (Fixes NumPy 2.0 build conflicts)
python -m pip install "numpy<2.0" Cython setuptools

# Compile scikit-surprise locally without isolated environment overrides
python -m pip install scikit-surprise --no-build-isolation

# Staging remaining framework dependencies
python -m pip install -r requirements.txt