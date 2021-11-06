import numpy as np
import pandas as pd
import pickle
from pathlib import Path
import os
from db.connection import get_df

# 두 함수에 모두 사용되기 때문에 전역 변수로 설정
df = get_df('course_fillna')


def cal_sim_score(title):

    dirpath = Path(__file__).parent.parent
    with open(os.path.join(dirpath, "preprocessing", "cos_sim.txt"), "rb") as f:
        cos_sim = pickle.load(f)
    indices = pd.Series(df.index, index=df['title'])
    idx = indices[title]

    sim_scores = np.array(cos_sim[idx])  # vectorized 연산 위해 numpy array로 변환
    if sim_scores.shape[0] != len(df):
        sim_score = np.zeros(len(df), )
        for s in range(sim_scores.shape[0]):
            sim_score += sim_scores[s]

        sim_score /= len(sim_scores)

        sim_scores = sim_score

    return sim_scores


def add_sim(title_list):
    sim_total = np.zeros(len(df), )
    for i in title_list:
        sim_total += cal_sim_score(i)

    # 정규화
    sim_norm = sim_total / len(title_list)

    sim_norm = np.round(sim_norm, 4)
    sim_norm = list(enumerate(sim_norm))
    return sim_norm


