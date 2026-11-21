import os
import numpy as np
import pandas as pd
import pickle
from pathlib import Path
from collections import defaultdict
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split

BASE = Path(__file__).resolve().parents[1]
DATA_DIR = BASE / 'data' / 'ml-latest-small'
MODEL_DIR = BASE / 'models'

def get_precision_recall_at_k(predictions, k=10, threshold=3.5):
    """Return precision and recall at k metrics for each user."""
    # First map the predictions to each user.
    user_est_true = defaultdict(list)
    for uid, _, true_r, est, _ in predictions:
        user_est_true[uid].append((est, true_r))

    precisions = dict()
    recalls = dict()
    for uid, user_ratings in user_est_true.items():
        # Sort user ratings by estimated value
        user_ratings.sort(key=lambda x: x[0], reverse=True)

        # Number of relevant items
        n_rel = sum((true_r >= threshold) for (_, true_r) in user_ratings)

        # Number of recommended items in top K
        n_rec_k = sum((est >= threshold) for (est, _) in user_ratings[:k])

        # Number of relevant and recommended items in top K
        n_rel_and_rec_k = sum(
            ((true_r >= threshold) and (est >= threshold))
            for (est, true_r) in user_ratings[:k]
        )

        # Precision@K: Proportion of recommended items that are relevant
        precisions[uid] = n_rel_and_rec_k / n_rec_k if n_rec_k != 0 else 0

        # Recall@K: Proportion of relevant items that are recommended
        recalls[uid] = n_rel_and_rec_k / n_rel if n_rel != 0 else 0

    return precisions, recalls

def calculate_ndcg_at_k(predictions, k=10):
    """Calculates the Normalized Discounted Cumulative Gain at K."""
    user_est_true = defaultdict(list)
    for uid, _, true_r, est, _ in predictions:
        user_est_true[uid].append((est, true_r))
        
    ndcgs = []
    for uid, user_ratings in user_est_true.items():
        if len(user_ratings) < 2:
            continue
            
        # Sort by predicted score to calculate DCG
        user_ratings.sort(key=lambda x: x[0], reverse=True)
        dcg = 0
        for i, (_, true_r) in enumerate(user_ratings[:k]):
            dcg += (2**true_r - 1) / np.log2(i + 2)
            
        # Sort by actual true rating to calculate Ideal DCG (IDCG)
        user_ratings.sort(key=lambda x: x[1], reverse=True)
        idcg = 0
        for i, (_, true_r) in enumerate(user_ratings[:k]):
            idcg += (2**true_r - 1) / np.log2(i + 2)
            
        if idcg > 0:
            ndcgs.append(dcg / idcg)
            
    return np.mean(ndcgs) if ndcgs else 0

def run_evaluation():
    ratings_path = DATA_DIR / 'ratings.csv'
    if not ratings_path.exists():
        print(f"❌ Error: Cannot find ratings dataset at {ratings_path}")
        return

    print("📊 Loading MovieLens ratings data...")
    ratings = pd.read_csv(ratings_path)
    
    # Define rating scale matching MovieLens (0.5 to 5.0)
    reader = Reader(rating_scale=(0.5, 5.0))
    data = Dataset.load_from_df(ratings[['userId', 'movieId', 'rating']], reader)
    
    # 80% Training Data, 20% Unseen Testing Data
    trainset, testset = train_test_split(data, test_size=0.2, random_state=42)
    
    # Load your existing model or retrain a test version
    print("🤖 Running SVD engine predictions on testing split...")
    algo = SVD(n_factors=100, random_state=42)
    algo.fit(trainset)
    predictions = algo.test(testset)
    
    # Calculate Metrics
    print("\n📈 Computing Performance Metrics...")
    precisions, recalls = get_precision_recall_at_k(predictions, k=10, threshold=3.5)
    
    mean_precision = np.mean(list(precisions.values()))
    mean_recall = np.mean(list(recalls.values()))
    mean_ndcg = calculate_ndcg_at_k(predictions, k=10)
    
    # Print the Evaluation Report Matrix
    print("="*50)
    print("🎬 CINESCOPE RECOMMENDATION ENGINE EVALUATION REPORT")
    print("="*50)
    print(f"• Precision@10: {mean_precision:.4f} (How many recommended items were good)")
    print(f"• Recall@10:    {mean_recall:.4f} (How many total good items we found)")
    print(f"• NDCG@10:      {mean_ndcg:.4f} (How optimal was the ranking order)")
    print("-"*50)
    print("Interpretation:")
    print(f"An NDCG of {mean_ndcg:.2f} means your system ranks highly relevant choices")
    print("near the top slots effectively compared to random distribution layouts.")
    print("="*50)

if __name__ == '__main__':
    run_evaluation()