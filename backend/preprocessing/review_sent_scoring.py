import pandas as pd
import numpy as np
from pathlib import Path
import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from preprocessing.review_pos_neg import clean_df, tokenizing


def tfidf():
    corpus = list(df.review)
    tfidfv = TfidfVectorizer(tokenizer=tokenizing, ngram_range=(2,2)) # bi-gram & tf-idf
    tfidfv.fit(corpus)
    df1 = tfidfv.transform(corpus).toarray()
    dataframe = pd.DataFrame(df1, columns = sorted(tfidfv.vocabulary_))
    return dataframe


def scoring():
    with open(os.path.join(dirpath, "preprocessing", "pos_list.pkl"), "rb") as f:
        pos = pickle.load(f)
    with open(os.path.join(dirpath, "preprocessing", "neg_list.pkl"), "rb") as f:
        neg = pickle.load(f)

    dataframe = tfidf()
    pos_df = dataframe[pos]
    pos_df.assign(pos_sum=pos_df.sum(axis=1)) # 긍정단어

    neg_df = dataframe[neg]
    neg_df.assign(neg_sum=neg_df.sum(axis = 1)) # 부정단어

    score = []
    for i in range(len(pos_df)): # 감성 점수 계산
        if (pos_df.loc[i, 'posSum'] + neg_df.loc[i, 'negSum']) != 0:
            score.append(((pos_df.loc[i, 'posSum'] - neg_df['negSum'][i]) / (pos_df.loc[i, 'posSum'] + neg_df.loc[i, 'negSum'])))

    score = np.array(score)

    new_score = df.avg_rate.to_numpy(dtype=float) + score

    return new_score


def concat_to_list():
    df['new_score'] = scoring()
    grouped_df = df.groupby('title').mean()
    new_score = list(grouped_df.new_score)
    return new_score


if __name__ == "__main__":
    df = clean_df()
    new_score = concat_to_list()
    dirpath = Path(__file__).parent.parent
    with open(os.path.join(dirpath, "preprocessing", "score.pkl"), "wb") as f:
        pickle.dump(new_score, f)