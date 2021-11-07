from db.db_connection.connection import get_df
from model.sugang_info import get_sugang_info
from model.course_scoring import add_sim


def top_n(n=10):
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
        if cnt == n:
            break

    recommend = df.iloc[top_idx].reset_index(drop=True)
    recommend['similarity'] = [i[1] for i in course_sim if i[0] in top_idx]

    return recommend


if __name__ == "__main__":
    print(top_n())