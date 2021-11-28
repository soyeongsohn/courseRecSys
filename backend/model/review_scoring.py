import pickle
import os
from pathlib import Path
from preprocessing.review_detailed_scoring import score2text


def filter_df():
    dirpath = Path(__file__).parent.parent
    with open(os.path.join(dirpath, "preprocessing", "score.pkl"), "rb") as f:
        new_score = pickle.load(f)

    final_df = score2text()
    final_df['new_score'] = new_score
    final_df['final_score'] = round(final_df['new_score'] + final_df['detailed_score'], 1)

    return final_df
