from bs4 import BeautifulSoup
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoAlertPresentException, UnexpectedAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re
import pandas as pd
from time import sleep
import os
from db.db_connection.connection import sql_conn


def get_driver():
    global driver
    os.environ['WDM_LOG_LEVEL'] = '0'
    options = ChromeOptions()
    options.add_argument("--incognito")
    options.add_argument("headless")
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    driver = Chrome(ChromeDriverManager().install(), options=options)
    return driver


# 로그인
def login(username, password):
    driver = get_driver()
    driver.get('https://sugang.konkuk.ac.kr/')
    WebDriverWait(driver, 5).until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'Main')))
    login_button = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#btn-login')))
    driver.find_element_by_name("stdNo").clear()
    driver.find_element_by_name("stdNo").send_keys(username)
    driver.find_element_by_name("pwd").clear()
    driver.find_element_by_name("pwd").send_keys(password)
    login_button.click()
    sleep(0.3)
    try:
        alert = driver.switch_to.alert
        alert.accept()
        return False
    except NoAlertPresentException:
        return True
    except UnexpectedAlertPresentException:
        return False


def logout():
    driver.close()
    return True


def grade_converter(grade):  # 학점을 숫자로 변환
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
    elif grade == 'P':  # 패논패 과목의 pass는 A+과 같게 평가 (패논패는 대체로 꿀과목이므로)
        return 4.5
    else:
        return 0.0


def get_data():
    WebDriverWait(driver, 5).until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'coreMain')))
    driver.execute_script("javascript:fnMenuLoad('/search?attribute=searchMain',this.id);")
    menu = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#sTabs > li:nth-child(4)')))
    menu.click()
    dom = BeautifulSoup(driver.page_source, 'lxml')
    table = dom.find_all("tr", role="row")
    stdno = re.findall(r'<label>학번</label>\n<span>([0-9]+?)</span>', str(dom))[0]
    dept = re.findall(r'소속</label>\n<span>([가-힣]+?)</span>', str(dom))[0]
    data = []
    for i in range(len(table)):
        try:
            course = re.findall(
                r'<td aria-describedby="gridRegisteredCredits_pobt_div_nm" role="gridcell" style="text-align:center;" title="([가-힣]{2})">',
                str(table[i]))[0]
            if course != '심교':
                continue
            else:
                title = re.findall(
                    r'<td aria-describedby="gridRegisteredCredits_cors_nm" role="gridcell" style="text-align:left;" title="([\w\W]+?)">',
                    str(table[i]))[0]
                if title == "심교":  # 학점 인정 과목
                    continue
                courseno = re.findall(
                    r'<td aria-describedby="gridRegisteredCredits_haksu_id" role="gridcell" style="text-align:center;" title="([\w\W]+?)">',
                    str(table[i]))[0]
                grade = re.findall(
                    r'<td aria-describedby="gridRegisteredCredits_grd" role="gridcell" style="text-align:center;" title="([A-Z]\+?)">',
                    str(table[i]))[0]
        except Exception:
            continue
        data.append((stdno, dept, title, courseno, grade_converter(grade)))
    return data


def to_df(data):
    df = pd.DataFrame(data, columns=['stdno', 'dept', 'title', 'courseno', 'grade'])
    return df


def load_to_db(data):
    conn, curs = sql_conn()

    insert_sql = """INSERT IGNORE INTO std_info (stdno, dept, title, courseno, grade)
                    VALUES (%s, %s, %s, %s, %s)"""

    curs.executemany(insert_sql, data)
    conn.commit()

    curs.close()
    conn.close()


def get_sugang_info():
    data = get_data()
    if len(data) != 0:
        df = to_df(data)
        load_to_db(data)
        return df[['title', 'grade']]  # 추천모델에서 사용하는 열만 리턴
    else:
        return None
