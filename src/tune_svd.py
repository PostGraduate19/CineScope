import pandas as pd
from surprise import Dataset, Reader, SVD
from surprise.model_selection import GridSearchCV

# 1. Load Data
DATA_PATH = "data/ml-latest-small/ratings.csv"
df = pd.read_csv(DATA_PATH)
reader = Reader(rating_scale=(0.5, 5.0))
data = Dataset.load_from_df(df[['userId', 'movieId', 'rating']], reader)

# 2. Define Parameter Grid
param_grid = {
    'n_epochs': [20, 30],
    'lr_all': [0.005, 0.01],
    'reg_all': [0.05, 0.1]
}

print("⚙️ Running Grid Search Cross-Validation...")
gs = GridSearchCV(SVD, param_grid, measures=['rmse'], cv=3, n_jobs=-1)
gs.fit(data)

# 3. Output Best Results
print(f"🏆 Best RMSE achieved: {gs.best_score['rmse']:.4f}")
print("💡 Optimal Hyperparameters to use:")
print(gs.best_params['rmse'])