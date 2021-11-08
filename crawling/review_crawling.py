from bs4 import BeautifulSoup
import re
from requests import request
from requests.sessions import Session
import pymysql
import sqlalchemy
import pandas as pd
import json
from db.connection import db_conn, get_df


def get_cookies():
    with open("../cookies.txt", 'r', encoding="utf-8") as f:
        lines = f.readlines()
    et = (' ').join(lines).split()

    session.cookies.clear()

    s = 0
    for i in [i for i, _ in enumerate(et) if _ == 'Medium']:
        e = i

        session.cookies.set(et[s], et[s + 1], domain=et[s + 2], path=et[s + 3])

        s = e + 1


def get_review_id():
    global session
    session = Session()
    get_cookies()

    review_id = []
    df = get_df('course_total')

    for i in range(len(df)):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
        }
        params = {
            'keyword': f'{df["title"][i]}'
        }
        url = "https://api.everytime.kr/find/lecture/list/keyword"
        resp = session.request(url=url, headers=headers, params=params, method='POST', cookies=session.cookies)
        dom = BeautifulSoup(resp.text, 'lxml')
        pname = re.findall(r'professor_name="(.+?)"', str(dom))
        rid = re.findall(r' id="([0-9]+?)"', str(dom))
        if df['profname'][i] in pname:
            review_id.append(rid[pname.index(df['profname'][i])])
  
    return review_id


def get_review(review_id):
    # 데이터프레임 생성
    review = pd.DataFrame(
        columns=['title', 'profname', 'grade', 'homework', 'teamwork', 'exam_time', 'avg_rate', 'like', 'dislike',
                 'review'])

    for i in range(len(review_id)):
        row = {}
        url = 'https://api.everytime.kr/find/lecture/article/list'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
        }
        params = {
            'school_id': '17',
            'limit_num': '200',
            'lecture_id': f'{review_id[i]}'
        }
        resp = session.request(url=url, headers=headers, params=params, method='POST', cookies=session.cookies)
        dom = BeautifulSoup(resp.text, 'lxml')

        # 한 강의 당 한 개의 데이터만 있는 정보들
        row['title'] = re.findall(r'name="([\S\s]+?)"', str(dom))[0]
        row['profname'] = re.findall(r'professor="([\S\s]+?)"', str(dom))[0]
        row['grade'] = re.findall(r'grade="([\S\s]+?)"', str(dom))[0]
        row['homework'] = re.findall(r'homework="([\S\s]+?)"', str(dom))[0]
        row['teamwork'] = re.findall(r'team="([\S\s]+?)"', str(dom))[0]
        row['exam_time'] = re.findall(r'exam_times="([\S\s]+?)"', str(dom))[0]

        # 한 강의 당 여러 개의 데이터가 있는 정보들(길이는 같음)
        reviews = re.findall(r'text="([\S\s]+?)"', str(dom))
        negv = re.findall(r'negvote="([0-9]+?)"', str(dom))
        posv = re.findall(r'posvote="([0-9]+?)"', str(dom))
        rate = re.findall(r'rate="([0-9]+?)"', str(dom))

        for i in range(len(reviews)):
            row['avg_rate'] = rate[i]
            row['like'] = posv[i]
            row['dislike'] = negv[i]
            row['review'] = reviews[i]
            # 데이터프레임에 데이터 추가
            review = review.append(row, ignore_index=True)

    return review


def load_to_db(df, filename):
    with open("../db_private.json") as f:
        db_info = json.load(f)
    conn = pymysql.connect(host=db_info['host'], user=db_info['user'], password=db_info['password'], db=db_info['db_connection'])
    curs = conn.cursor(pymysql.cursors.DictCursor)

    drop_sql = f"""drop table if exists {filename}; """
    curs.execute(drop_sql)
    conn.commit()

    database_connection = db_conn(db_info)
    df.to_sql(con=database_connection, name=filename, if_exists='replace')

    curs.close()
    conn.close()
    df.to_pickle(f'./data/{filename}.pkl') # backup just in case


if __name__ == "__main__":
    review_id = get_review_id()
    df = get_review(review_id)
    load_to_db(df, 'review')
