import pandas as pd
from db.db_connection.connection import get_df
from model.sugang_info import get_sugang_info
from model.course_scoring import add_sim
from model.review_scoring import filter_df


def top_n():
    df = get_df('course_fillna')
    sugang_info = get_sugang_info()
    title_list = list(sugang_info['title'])
    grade_list = list(sugang_info['grade'])
    course_sim = sorted(add_sim(title_list, grade_list), key=lambda x: x[1], reverse=True)
    rank_idx = [i[0] for i in course_sim]
    course_2021 = get_df('course_2021')
    title_2021 = list(course_2021['title'])
    profname_2021 = list(course_2021['profname'])

    ignore = list(df.loc[df.title.isin(title_list)].index)
    ig_subcode = list(df.loc[df.title.isin(title_list), 'subcode'])
    ig_subcode = list((filter(lambda x: x != '', ig_subcode)))

    cnt = 0
    top_idx = []
    for i in rank_idx:
        if i in ignore:
            continue
        if df['subcode'][i] in ig_subcode:
            continue

        if df['title'][i] in ignore:
            continue

        elif (df['title'][i] in title_2021) and (df['profname'][i] in profname_2021):
            if title_2021.index(df['title'][i]) == profname_2021.index(df['profname'][i]):
                top_idx.append(i)
                cnt += 1
        if cnt == 10:
            break

    recommend = df.iloc[top_idx].reset_index(drop=True)
    recommend['similarity'] = [i[1] for i in course_sim if i[0] in top_idx]

    return recommend


def final_result():
    df = top_n()
    # 리뷰 scoring 한 후 추가해야 함
    review_df = filter_df()
    review_df.loc[review_df.title.isin(df.title)]
    final_df = df.merge(review_df, on="title", how="inner")
    final_df.sort_values(by="final_score", ascending=False, inplace=True)
    final_df.rename(columns={'title': '강의명', 'profname': '교수명', 'domain': '영역', 'field': '학문분야',
                             'grade': '학점', 'homework': '과제', 'teamwork': '팀플', 'exam_time': '시험 횟수',
                             'avg_rate': '평점'}, inplace=True)

    return final_df[['강의명', '교수명', '영역', '학문분야', '학점', '과제', '팀플', '시험 횟수', '평점']][:4]