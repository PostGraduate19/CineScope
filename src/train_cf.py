from pathlib import Path
import pandas as pd
import pickle
from surprise import Dataset, Reader, SVD
from surprise.model_selection import cross_validate

BASE = Path(__file__).resolve().parents[1]
DATA_DIR = BASE / 'data' / 'ml-latest-small'
MODEL_DIR = BASE / 'models'

def train_svd():
    print("Loading ratings data...")
    ratings = pd.read_csv(DATA_DIR / 'ratings.csv')
    
    # Surprise requires a specific reader format (user, item, rating)
    reader = Reader(rating_scale=(0.5, 5.0))
    data = Dataset.load_from_df(ratings[['userId', 'movieId', 'rating']], reader)
    
    print("Training SVD Matrix Factorization model...")
    # Initialize SVD with 100 latent factors
    algo = SVD(n_factors=100, random_state=42)
    
    # Build full trainset and fit
    trainset = data.build_full_trainset()
    algo.fit(trainset)
    
    # Save the trained model
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODEL_DIR / 'svd_model.pkl', 'wb') as f:
        pickle.dump(algo, f)
        
    print("Model saved to models/svd_model.pkl successfully.")

if __name__ == '__main__':
    train_svd()