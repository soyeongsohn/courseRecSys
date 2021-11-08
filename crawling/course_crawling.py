from bs4 import BeautifulSoup
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import re
from time import sleep
import pandas as pd
import numpy as np
import pymysql
import sqlalchemy
from pathlib import Path
from os import path
import json
from db.connection import db_conn


def get_driver():
    options = ChromeOptions()
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    options.add_argument("--incognito")
    options.add_argument("headless")
    global driver
    driver = Chrome(ChromeDriverManager().install(), options=options)
    return driver


def get_course(year):
    global course
    global driver
    driver = get_driver()
    driver.get('https://bulletins.konkuk.ac.kr/ko-KR/CultureSearch/Culture/Advanced_Culture/')
    driver.find_element_by_xpath(f'/html/body/div[4]/div/div/div/div/div[2]/a[2]').click()
    driver.find_element_by_xpath(f'/html/body/div[4]/div/div/div/div/div[2]/a[3]').click()
    if year == 2021:
        no = 1
    elif year == 2020:
        no = 2
    elif year == 2019:
        no = 3

    courses = []
    data_id = []  # 추후 과목 세부 정보 페이지 이동하기 위함
    while True:
        sleep(3) # 컴퓨팅 파워에 따라 달라질듯
        WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "entitylist")))
        dom = BeautifulSoup(driver.page_source, 'lxml')
        course = dom.select(
            f'body > div.container > div > div > div > div > div.col-md-12.columnBlockLayout > l.l{no} > div > div.entity-grid.entitylist > div.view-grid.has-pagination > table > tbody > tr')
        for i in course:
            data_id.append(re.findall(r'data-id="(.+?)"', str(i))[0])
            course_info = re.findall(r'data-value="(.+?)"', str(i))
            col = re.findall(r'data-th="(.+?)"', str(course))
            cols = [i for n, i in enumerate(col) if i not in col[:n]]
            if len(cols) - 1 > len(course_info):
                course_info.extend([np.nan, np.nan])  # 학문분야가 공백인 경우 nan 값으로 채우기(한, 영 이므로 2개)
            courses.append(course_info)
        if driver.find_elements_by_link_text('>')[no-1].get_attribute('aria-disabled') == 'true':  # 마지막 페이지에 도달한 경우
            break
        driver.find_elements_by_link_text('>')[no-1].click()

    course = pd.DataFrame(courses, columns=['title', 'eng_title', 'semester', 'courseno', 'div', 'grade',
                                            'credit', 'hours', 'dept', 'domain', 'field', 'eng_field'])
    return data_id


def get_details(data_id):
    # 새로 추가할 열 추가
    global course
    global driver
    course = course.reindex(columns=course.columns.tolist() + ['description', 'profname', 'field(L)', 'subcode'])
    for i in range(len(data_id)):

        driver.get(f'https://bulletins.konkuk.ac.kr/ko-KR/department/LIBERAL_ARTS/searchresultpage1/?id={data_id[i]}')
        sleep(1.5)
        dom = BeautifulSoup(driver.page_source, 'lxml')
        try:
            desc = re.findall(r'>(.+?)</textarea>', str(dom.select('#new_description')[0]).replace('\r\n', ' '))[0]
        except Exception:
            try:
                desc = re.findall(r'>(.+?)\t', str(dom.select('#new_description')[0]).replace('\r\n', ' '))[0]
            except Exception:
                desc = re.findall(r'>(.+?)\n', str(dom.select('#new_description')[0]).replace('\r\n', ' '))[0]

        course.loc[i, 'description'] = desc
        code = dom.find("label", {'id': 'new_code_label'}).find_parent().find_next_sibling().find_next().text
        # 동일 과목 대체 코드가 없으면 빈 문자열을 리턴하므로 대체 코드 유무에 관계없이 append

        course.loc[i, 'subcode'] = code

        prof = dom.find_all('td', {'data-attribute': 'new_professor'})
        p = list((set([re.findall(r'data-value="(.+?)"', str(_))[0] for _ in prof])))

        course.loc[i, 'profname'] = (', ').join(p)

        fields = dom.select('#sub_part > div > div.view-grid > table > tbody > tr > td')
        l = list(set([_.attrs['aria-label'] for _ in fields if _.attrs['data-th'] == '학문분야(대)']))

        course.loc[i, 'field(L)'] = (', ').join(l)


def load_to_db(year):
    conn = pymysql.connect(host=db_info['host'], user=db_info['user'], password=db_info['password'], db=db_info['db'])
    curs = conn.cursor(pymysql.cursors.DictCursor)

    drop_sql = f"""drop table if exists course_{year}; """
    curs.execute(drop_sql)
    conn.commit()

    database_connection = db_conn(db_info)

    course.to_sql(con=database_connection, name=f'course_{year}', if_exists='replace', index=False,
                  dtype={'courseno': sqlalchemy.sql.sqltypes.CHAR(9), 'credit': sqlalchemy.types.INTEGER(),
                         'domain': sqlalchemy.sql.sqltypes.VARCHAR(12)})

    # 학수번호(courseno)를 primary key로 지정
    sql = f"""alter table course_{year} add PRIMARY KEY (courseno);"""
    curs.execute(sql)
    conn.commit()

    curs.close()
    conn.close()


def get_data(year):
    global course
    # driver = get_driver()
    data_id = get_course(year)
    get_details(data_id)
    course.drop(['eng_title', 'div', 'grade', 'hours', 'dept', 'field', 'eng_field'], axis=1, inplace=True)
    to_drop = [i for i in range(len(course)) if re.sub(r'[^\w]', '',course['description'][i]).encode().isalpha()]  # 영문 description (외국인 대상 과목) 제거
    course.drop(to_drop, axis=0, inplace=True)
    course.reset_index(drop=True, inplace=True)
    course.rename(columns={'field(L)': 'field'}, inplace=True)
    load_to_db(year)
    # save backup just in case
    fliepath = Path(__file__).parent
    course.to_pickle(path.join(fliepath, 'data',f"course_{year}.pkl"))


def data_join():
    conn = pymysql.connect(host=db_info['host'], user=db_info['user'], password=db_info['password'], db=db_info['db_connection'])
    curs = conn.cursor(pymysql.cursors.DictCursor)
    sql = """SELECT * from course_2019"""
    course_2019 = pd.read_sql(sql, conn)
    sql = """SELECT * from course_2020"""
    course_2020 = pd.read_sql(sql, conn)
    sql = """SELECT * from course_2021"""
    course_2021 = pd.read_sql(sql, conn)

    course = pd.concat([course_2019, course_2020, course_2021], ignore_index=True)

    # 교수명 비어있는 교과목 삭제
    to_drop = [i for i in range(len(course)) if course['profname'][i] == '']
    course.drop(to_drop, axis=0, inplace=True)

    course = course.assign(profname=course['profname'].str.split(',')).explode('profname').reset_index(drop=True)
    course.drop_duplicates(subset=['courseno', 'profname'], inplace=True)
    course.reset_index(drop=True, inplace=True)
    database_connection = db_conn(db_info)
    course.to_sql(con=database_connection, name='course_total', if_exists='replace', index=False,
                  dtype={'courseno': sqlalchemy.sql.sqltypes.CHAR(9), 'credit': sqlalchemy.types.INTEGER(),
                         'domain': sqlalchemy.sql.sqltypes.VARCHAR(12),
                         'profname': sqlalchemy.sql.sqltypes.VARCHAR(10)})
    sql = """alter table course_total add PRIMARY KEY (courseno, profname);"""
    curs.execute(sql)
    conn.commit()

    fliepath = Path(__file__).parent
    course.to_pickle(path.join(fliepath, 'data', 'course_total.pkl'))  # save back up just in case

    curs.close()
    conn.close()


if __name__ == "__main__":
    with open("../db_private.json") as f:
        db_info = json.load(f)
    years = [2019, 2020, 2021]
    for year in years:
        get_data(year)
    data_join()
