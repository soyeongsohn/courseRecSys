from bs4 import BeautifulSoup
import re
from requests.sessions import Session
import pandas as pd


def get_cookies():
    str_ = '''
    copy cookies from devtools > application
    '''
    et = str_.split()
    session.cookies.clear()

    s = 0
    for i in [i for i, _ in enumerate(et) if _ =='Medium']:
        e = i
    
        session.cookies.set(et[s], et[s+1], domain=et[s+2], path=et[s+3])
    
        s = e + 1
        
def get_review_id():
    global session
    session = Session()
    get_cookies()
    
    review_id = []
    df = pd.read_pickle('./data/course_total.pkl')
    
    for i in range(len(df)):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
        }
        params={
            'keyword': f'{df["교과목명"][i]}'
        }
        url = "https://api.everytime.kr/find/lecture/list/keyword"
        resp = session.request(url=url, headers=headers, params=params, method='POST', cookies=session.cookies)
        dom = BeautifulSoup(resp.text, 'lxml')
        pname = re.findall(r'professor_name="(.+?)"', str(dom))
        rid = re.findall(r' id="([0-9]+?)"', str(dom))
        if df['교수명'][i] in pname:
            review_id.append(rid[pname.index(df['교수명'][i])])
    
    return review_id

def get_review(review_id):
    # 데이터프레임 생성
    review = pd.DataFrame(columns=['교과목명', '교수명', '성적부여', '과제', '팀플', '시험횟수', '평점', '추천수', '반대수', '리뷰'])

    for i in range(len(review_id)):
        row = {}
        url = 'https://api.everytime.kr/find/lecture/article/list'
        headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
            }
        params={
                'school_id': '17',
                'limit_num' : '200',
                'lecture_id': f'{review_id[i]}'
            }
        resp = session.request(url=url, headers=headers, params=params, method='POST', cookies=session.cookies)
        dom = BeautifulSoup(resp.text, 'lxml')

        # 한 강의 당 한 개의 데이터만 있는 정보들
        row['교과목명'] = re.findall(r'name="([\S\s]+?)"', str(dom))[0]
        row['교수명'] = re.findall(r'professor="([\S\s]+?)"', str(dom))[0]
        row['성적부여'] = re.findall(r'grade="([\S\s]+?)"', str(dom))[0]
        row['과제'] = re.findall(r'homework="([\S\s]+?)"', str(dom))[0]
        row['팀플'] = re.findall(r'team="([\S\s]+?)"', str(dom))[0]
        row['시험횟수'] = re.findall(r'exam_times="([\S\s]+?)"', str(dom))[0]

        # 한 강의 당 여러 개의 데이터가 있는 정보들(길이는 같음)
        reviews = re.findall(r'text="([\S\s]+?)"', str(dom))
        negv = re.findall(r'negvote="([0-9]+?)"', str(dom))
        posv = re.findall(r'posvote="([0-9]+?)"', str(dom))
        rate = re.findall(r'rate="([0-9]+?)"', str(dom))

        for i in range(len(reviews)):
            row['평점'] = rate[i]
            row['추천수'] = posv[i]
            row['반대수'] = negv[i]
            row['리뷰'] = reviews[i]

            # 데이터프레임에 데이터 추가
            review = review.append(row, ignore_index=True)
            
    return review

if __name__ == "__main__":
    review_id = get_review_id()
    review = get_review(review_id)
    review.to_pickle('./data/review.pkl')

