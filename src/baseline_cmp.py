import pandas as pd
from pathlib import Path
from surprise import Dataset, Reader, NormalPredictor, BaselineOnly, SVD, accuracy
from surprise.model_selection import train_test_split

# 1. Path Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data' / 'ml-latest-small'
RATINGS_FILE = DATA_DIR / 'ratings.csv'

if not RATINGS_FILE.exists():
    raise FileNotFoundError(f"Cannot find dataset at {RATINGS_FILE}. Ensure your data folder is configured correctly.")

print("📊 Loading MoviesLens dataset...")
ratings = pd.read_csv(RATINGS_FILE)

# 2. Surprise Dataset Initialization
reader = Reader(rating_scale=(0.5, 5.0))
data = Dataset.load_from_df(ratings[['userId', 'movieId', 'rating']], reader)

# 3. Universal Train/Test Split
print("✂️ Splitting data into 80% training and 20% testing...")
trainset, testset = train_test_split(data, test_size=0.2, random_state=42)

results = {}

# --- ALGORITHM 1: The Random Baseline (Floor) ---
print("\n⚙️ Executing Random Predictor (Baseline 1)...") 
algo_random = NormalPredictor()
algo_random.fit(trainset)
predictions_random = algo_random.test(testset)
results['Random Guess (NormalPredictor)'] = accuracy.rmse(predictions_random, verbose=False)

# --- ALGORITHM 2: The Statistical Mean Baseline ---
print("⚙️ Executing Statistical Mean (Baseline 2)...")
bsl_options = {'method': 'als', 'n_epochs': 5, 'reg_u': 12, 'reg_i': 5}
algo_baseline = BaselineOnly(bsl_options=bsl_options)
algo_baseline.fit(trainset)
predictions_baseline = algo_baseline.test(testset)
results['Statistical Average (BaselineOnly)'] = accuracy.rmse(predictions_baseline, verbose=False)

# --- ALGORITHM 3: Optimized Advanced Matrix Factorization ---
print("⚙️ Executing Matrix Factorization (Final Model)...")
# Injecting optimized hyperparameters discovered via Grid Search Cross-Validation
algo_svd = SVD(n_epochs=30, lr_all=0.005, reg_all=0.06, random_state=42)
algo_svd.fit(trainset)
predictions_svd = algo_svd.test(testset)
results['Matrix Factorization (SVD)'] = accuracy.rmse(predictions_svd, verbose=False)

# 4. Final Empirical Output
print("\n" + "="*50)
print("🏆 RMSE PERFORMANCE COMPARISON (Lower is Better)")
print("="*50)
for model, rmse_val in sorted(results.items(), key=lambda x: x[1], reverse=True):
    print(f"{model:<35} : {rmse_val:.4f}")
print("="*50)

# Calculate the exact improvement percentage
improvement = ((results['Statistical Average (BaselineOnly)'] - results['Matrix Factorization (SVD)']) / results['Statistical Average (BaselineOnly)']) * 100
print(f"\n💡Conclusion: SVD improved accuracy by {improvement:.2f}% over basic statistical averages.")