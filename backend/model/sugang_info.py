from bs4 import BeautifulSoup
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re
from time import sleep
import numpy as np
import pandas as pd
import pymysql
import json
from pathlib import Path
import os


class LoginFailedError(Exception):
    pass


def get_driver():
    global driver
    os.environ['WDM_LOG_LEVEL'] = '0'
    options = ChromeOptions()
    options.add_argument("--incognito")
    options.add_argument("headless")
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    driver = Chrome(ChromeDriverManager().install(), options=options)
    return driver


# 로그인
def login():
    for i in range(5):  # 5번 시도, 실패 시
        driver = get_driver();
        driver.get('https://kupis.konkuk.ac.kr/sugang/login/loginTop.jsp')
        login_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "form input[type=button]")))
        user_id = input("아이디를 입력하세요: ")
        pwd = input("비밀번호를 입력하세요: ")
        driver.find_element_by_name('stdNo').clear()
        driver.find_element_by_name('stdNo').send_keys(user_id)
        driver.find_element_by_name('pwd').clear()
        driver.find_element_by_name('pwd').send_keys(pwd)
        login_button.click()
        tmp = driver.window_handles[1]
        sleep(0.5)
        new_tab = driver.window_handles[1]
        if new_tab != tmp:
            driver.get('https://kupis.konkuk.ac.kr/sugang/login/mainBodyNew.jsp')
            driver.switch_to.window(driver.window_handles[1])
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            break
        else:
            print("로그인 실패")
            driver.quit()

    if i == 4:
        print('로그인을 5회 실패하였습니다. 포털에서 아이디 또는 비밀번호를 찾은 후 이용해주세요')
        raise LoginFailedError("Please restart after finding your login info")
        driver.quit()


def grade_converter(grade): # 학점을 숫자로 변환
    if grade == 'A+':
        return 4.5
    elif grade == 'A':
        return 4.0
    elif grade == 'B+':
        return 3.5
    elif grade == 'B':
        return 3.0
    elif grade == 'C+':
        return 2.5
    elif grade == 'C':
        return 2.0
    elif grade == 'D+':
        return 1.5
    elif grade == 'D':
        return 1.0
    elif grade == 'F':
        return 0.0
    elif grade == 'P': # 패논패 과목의 pass는 A+과 같게 평가 (패논패는 대체로 꿀과목이므로)
        return 4.5
    else:
        return 0.0


def get_data():
    stdinfo = re.findall(r'<span>(20[0-9]{7}.+?)\n', str(driver.page_source))[0].split()  # 학번, 학과

    driver.get('https://kupis.konkuk.ac.kr/sugang/acd/cour/aply/CourPersonPntInq.jsp')  # 취득학점 조회
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, 'table')))
    dom = BeautifulSoup(driver.page_source, 'lxml')
    course_list = np.array(dom.findAll('table')[0].findAll('td'))
    course_split = np.split(course_list, len(dom.findAll('table')[0].findAll('tr')) - 1)
    data = []
    for i in range(len(course_split)):
        if course_split[i][2][0] != "심교":
            continue
        else:
            data.append((stdinfo[0], stdinfo[1], course_split[i][4][0], course_split[i][3][0],
                         grade_converter(course_split[i][-1][0])))

    return data


def to_df(data):
    df = pd.DataFrame(data, columns=['stdno', 'dept', 'title', 'courseno', 'grade'])
    return df


def load_to_db(data):
    dirpath = Path(__file__).parent.parent.parent
    with open(os.path.join(dirpath, "db_private.json")) as f:
        db_info = json.load(f)


    conn = pymysql.connect(host=db_info['host'], user=db_info['user'], password=db_info['password'], db=db_info['db_connection'])
    curs = conn.cursor(pymysql.cursors.DictCursor)

    insert_sql = """INSERT INTO std_info (stdno, dept, title, courseno, grade)
                    VALUES (%s, %s, %s, %s, %s)"""

    curs.executemany(insert_sql, data)
    conn.commit()

    curs.close()
    conn.close()


def get_sugang_info():
    login()
    data = get_data()
    df = to_df(data)
    load_to_db(data)

    return df[['title', 'grade']] # 추천모델에서 사용하는 열만 리턴