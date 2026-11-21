# 🎬 CineScope: Your Smart Movie Buddy!

Welcome to **CineScope**! Imagine having a super-smart friend who has watched thousands of movies and knows *exactly* which movie you will love next. That is what CineScope does!

---

## 🌐 Play With CineScope Live Right Now!

You don't even need to install anything if you just want to test it out—**CineScope is live on Streamlit**! Click the link below, type a movie name or hit a **Mood Suggestor** button, and see what it picks for you:

👉 **[Launch CineScope on Streamlit](https://cinescopee.streamlit.app/)**

*(Heads-up: if the app has been sleeping for a bit, Streamlit might take a few seconds to wake it up—just give it a moment!)*

---

## 🧠 How Does CineScope Work?

CineScope uses two clever tricks to pick movies for you:

1. **The Genre Matcher (Content-Based Filtering):** If you like a movie with space battles and robots, CineScope looks at movie tags (like *Sci-Fi* and *Action*) to find other movies with the exact same ingredients.
2. **The Crowd Detective (Collaborative Filtering):** CineScope looks at how thousands of movie fans rated movies (`1` to `5` stars). If people who loved *Toy Story* also loved *Finding Nemo*, CineScope learns to suggest *Finding Nemo* to you too!

---

## 📁 What Is Inside This Folder?

Think of this project like a LEGO set. Every folder has its own special pieces:

```text
CineScope/
├── app.py                     # The main app screen you click and play with!
├── cinescope_pipeline.ipynb   # A science notebook where the movie brain is tested
├── requirements.txt           # The shopping list of Python tools we need
├── README.md                  # This instruction manual!
├── data/
│   └── ml-latest-small/       # The big book of 9,742 movies and 100,836 star ratings
│       ├── movies.csv
│       └── ratings.csv
├── models/                    # The saved "brain files" so the app loads super fast
│   ├── movies.pkl
│   ├── genre_matrix.pkl
│   └── svd_model.pkl
└── src/                       # The helper gears working behind the scenes
    ├── build_model.py         # Builds and saves the movie brain files
    ├── recommender.py         # Picks the best movies when you search
    └── database.py            # Remembers which movies you clicked "Like" on
```

---

## 🛠️ Step-by-Step: How to Set It Up and Run It!

Before you start, make sure **Python** is installed on your computer. Then open your terminal (like PowerShell in VS Code) inside the `CineScope` folder and follow these 4 easy steps!

### Step 1: Make a Safe Playground (Virtual Environment)
We create a clean little box called `.venv` so our project's tools don't get mixed up with anything else on your computer:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(When it works, you will see `(.venv)` appear at the start of your terminal line!)*

### Step 2: Install the Tools
Tell Python to download all the helper packages listed in `requirements.txt`:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Step 3: Build the Movie Brain (Optional)
If the `models/` folder is empty, run this command to train the movie brain and save its memory files:

```powershell
python -m src.build_model
```

### Step 4: Launch CineScope! 🚀
Run this magic command to open CineScope in your web browser:

```powershell
streamlit run app.py
```

Your browser will pop open automatically! Type any movie name in the search box—or click one of the **Mood Suggestor** buttons—and watch CineScope pick movies just for you.

---

## 🔑 Adding Movie Posters & Trailers (Optional)

CineScope uses a free key from **TMDB (The Movie Database)** to show movie posters, trailers, and where to watch them.

1. Create a folder named `.streamlit` inside `CineScope`.
2. Inside that folder, create a file named `secrets.toml`.
3. Paste your key inside like this:

```toml
TMDB_API_KEY = "paste_your_secret_key_here"
```

*(Never share your secret key online or upload `secrets.toml` to GitHub!)*