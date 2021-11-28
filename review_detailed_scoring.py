import pandas as pd
import numpy as np
from preprocessing.review_pos_neg import clean_df


def detailed_scoring():
    df = clean_df()
    def embedding_3(colname): return df[colname].apply(lambda x: 5 if x == "없음" else (3 if x == "보통" else 1))
    df.homework = embedding_3('homework')
    df.teamwork = embedding_3('teamwork')
    df.grade = df.grade.apply(lambda x: 5 if x == "학점느님" else(3.5 if x == "비율 채워줌" else (2.25 if x == "매우 깐깐함" else 1)))
    df.exam_time = df.exam_time.apply(lambda x: 5 if x == '없음' else(4 if x == '한 번' else (3 if x =='두 번' else (2 if x == '세 번' else 1))))
    df['detailed_score'] = df.grade * 0.4 + df.teamwork * 0.3 + df.homework * 0.2 + df.exam_time * 0.1

    grouped_df = df.groupby('title').mean().round(1)
    grouped_df.reset_index(level="title", inplace=True)
    return grouped_df


def score2text():
    df = detailed_scoring()
    def embedding(colname): return df[colname].apply(lambda x: "없음" if x == 5 else("보통" if x >= 3 else "많음"))
    df.homework = embedding('homework')
    df.teamwork = embedding('teamwork')
    df.grade = df.grade.apply(lambda x: "학점느님" if x > 4 else ("비율 채워줌" if x > 2.75 else ("매우 깐깐함" if x > 1.75 else "F 폭격기")))
    df.exam_time = df.exam_time.apply(lambda x: "없음" if x == 5 else ("한 번" if x >= 4 else ("두 번" if x >= 3 else ("세 번" if x >= 2 else "네 번 이상"))))

    return df






