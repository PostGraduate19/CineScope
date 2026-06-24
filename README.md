# 🎬 CineScope: Hybrid Personalized Recommender Engine

Here is the fully compiled, synchronized `README.md` for your project root. This version integrates the complete file mapping, environment setup fixes, hyperparameter details, ranking metrics, and execution steps while maintaining the concise, professional tone of your original blueprint.

---

```markdown
# 🎬 CineScope: Hybrid Movie Recommendation Engine

CineScope is an advanced Hybrid Movie Recommendation Engine designed to address data data sparsity and the cold-start problem in entertainment platforms. The system blends a **Content-Based Filtering Layer** (utilizing TF-IDF Genre Vectorization) with an optimized **Collaborative Filtering Layer** (utilizing Singular Value Decomposition Matrix Factorization). 

This repository houses the end-to-end data engineering, validation baseline tracking, hyperparameter optimization, database infrastructure, and artifact serialization pipeline.

---

## 📂 Complete Project Architecture

The workspace must be arranged according to the following layout parameters to ensure path normalization configurations resolve correctly across your execution context:

```text
cinescope-fresh/
│
├── .gitignore                      # Prevents tracking of environment, data, and models
├── app.py                          # Streamlit web-serving user interface application
├── README.md                       # System documentation and deployment runbook
├── requirements.txt                # Unified production dependency manifest
│
├── .venv/                          # Isolated project virtual environment
│
├── data/                           # Localized repository data volumes
│   └── ml-latest-small/            # MovieLens dataset extract
│       ├── movies.csv              # Content feature matrix metadata
│       └── ratings.csv             # Explicit interaction metrics
│
├── models/                         # Serialized binary storage volumes
│   ├── movies.pkl                  # Frozen DataFrame with processed features
│   ├── genre_matrix.pkl            # Compressed Sparse Row TF-IDF matrix
│   └── svd_model.pkl               # Trained SVD model weights and biases
│
├── notebook/
│   └── CineScope_Training_Pipeline.ipynb  # Unified interactive training and tuning suite
│
└── src/                            # Core modular production source engine
    ├── __init__.py                 # Treats the src directory as an importable module
    ├── baseline_cmp.py             # Script to run empirical error baseline calculations
    ├── build_model.py              # Orchestrator to generate all content and CF artifacts
    ├── database.py                 # SQLite database schema initialization and tracking
    ├── evaluate.py                 # Ranking metrics engine (Precision, Recall, NDCG)
    ├── recommender.py              # Hybrid blend calculator and recommendation serving layer
    ├── train_cf.py                 # Singular script to train Collaborative Filtering weights
    └── tune_svd.py                 # Grid search script to optimize SVD hyperparameters

```

---

## 🛠️ Environment Setup & Isolation

To bypass system-level path collisions and prevent corruption leakage from global Windows environment directories, run these commands inside your project root to initialize your isolated workspace:

```powershell
# 1. Create a fresh virtual environment
python -m venv .venv

# 2. Activate the environment path
.\.venv\Scripts\Activate.ps1

# 3. Purge cache and upgrade package manager
python -m pip cache purge
python -m pip install --upgrade pip

# 4. Ingest dependencies cleanly from the unified manifest
python -m pip install -r requirements.txt

```

---

## ⚙️ Modular Source Engine Architecture (`src/`)

Your production source scripts are decoupled into specialized operational modules:

* **`baseline_cmp.py`**: Runs the offline error tests comparing random prediction floors ($RMSE \approx 1.4191$) against the rigid statistical control average ($RMSE \approx 0.8733$).
* **`tune_svd.py`**: Executes a 3-Fold `GridSearchCV` over learning rates and regularization variables to discover optimized coordinates.
* **`train_cf.py`**: Trains the collaborative matrix factorization vectors over the finalized training splits.
* **`build_model.py`**: The central execution file that cleans text arrays, extracts TF-IDF keyword matrices, fits the optimized SVD engine, and dumps the resulting binaries into `models/`.
* **`evaluate.py`**: Computes validation matrices ($IR$ metrics) tracking top-10 Precision, Recall, and NDCG values.
* **`database.py`**: Hooks up a localized SQLite database engine to log interactive runtime queries, analytics metadata, and track system health.
* **`recommender.py`**: Extends hybrid algorithms to combine content rankings and collaborative ratings into a unified item stream score.

---

## ⚙️ The Unified Optimization Pipeline (`.ipynb`)

For exploratory development, all modular scripts are consolidated inside `notebook/CineScope_Training_Pipeline.ipynb`. Open this file in VS Code, connect it to your `.venv` kernel, and execute to see key performance boundaries:

### 1. Empirical Error Baseline Results

* **Random Guess (`NormalPredictor`):** Establishes the performance floor ($RMSE \approx 1.4191$).
* **Statistical Average (`BaselineOnly` via ALS):** Computes user-item rating deviations ($RMSE \approx 0.8733$).

### 2. Hyperparameter Optimization Results

Untuned SVD using default settings introduces massive error due to dataset sparsity ($RMSE \approx 0.8807$). Running optimization enforces these exact mathematical adjustments:

* **Learning Rate (`lr_all = 0.005`):** Prevents gradient descent from overshooting the global minimum down the loss landscape.
* **Regularization (`reg_all = 0.06`):** Penalizes noisy vector allocations across sparse data segments.
* **Epochs (`n_epochs = 30`):** Extended to ensure complete mathematical convergence stability.

This drives final `SVD` error down to an optimal **0.8690**, yielding a **+0.49% predictive improvement** over the baseline control.

### 3. Top-k Ranking Evaluation Metrics ($k=10$, Threshold $\ge 3.5$)

* **Mean Precision@10 (0.7446):** Verifies that $\approx 74.46\%$ of recommended items strictly align with user preference targets.
* **Mean Recall@10 (0.5086):** Measures the ratio of relevant movies successfully surfaced by the system.
* **Mean NDCG@10 (0.7949):** Confirms that at a **79.5% efficiency rate**, the algorithm correctly places high-match target content at the absolute top of the user viewport.

---

## 💾 Artifact Serialization & Production Staging

Upon running `python src/build_model.py` or executing the complete notebook, three key files are dropped into `models/` for immediate production inference access:

* `movies.pkl`: Cleaned strings mapping title features and space-separated tokens.
* `genre_matrix.pkl`: Compressed sparse representation vectors ready for real-time item similarity evaluation.
* `svd_model.pkl`: Compressed matrix coefficients used to generate prompt collaborative rating projections.

---

## 🚀 Running the User Interface Application

To deploy and test the user-facing recommendations on your local machine, run the following command to lift the Streamlit service:

```powershell
streamlit run app.py
