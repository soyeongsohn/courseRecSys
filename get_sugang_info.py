from bs4 import BeautifulSoup
from selenium.webdriver import Chrome, ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
import re
from time import sleep


def get_driver():
    options = ChromeOptions()
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    options.add_argument("--incognito")
    options.add_argument("headless")
    driver = Chrome(ChromeDriverManager().install(), options=options)
    return driver


# 로그인
def login(driver):
    for i in range(5):  # 5번 시도, 실패 시
        driver.get('https://wein.konkuk.ac.kr/common/user/login.do')
        sleep(0.1)
        userId = input("아이디를 입력하세요: ")
        pw = input("비밀번호를 입력하세요: ")
        driver.find_element_by_name('userId').clear()
        driver.find_element_by_name('userId').send_keys(userId)
        driver.find_element_by_name('pw').clear()
        driver.find_element_by_name('pw').send_keys(pw)
        driver.find_element_by_css_selector('#loginBtn').click()
        try:
            # 팝업창 닫기
            driver.find_element_by_css_selector(
                '#container > div.popup_main.open > div > div.right_box > div.bottom_box > button.btn_today').click()
            break
        except Exception:
            print("로그인 실패")
    if i == 4:
        print('로그인을 5회 실패하였습니다. 다음에 다시 이용해주세요')
        driver.close()
        return False
    else:
        return True


def std_info(driver):
    dom = BeautifulSoup(driver.page_source, 'lxml')
    info = dom.find(attrs={'class': 'line01_01 first'})
    stdno = re.findall(r'[가-힣]\(([0-9]{9})', str(info))[0]
    dept = re.findall(r'"text02">(.+?)/[0-9]', str(info))[0]
    return stdno, dept


# 교양 수강 내역 과목 페이지 돌면서 정보 크롤링
def get_subj(driver):
    i = 1
    table = []
    while True:
        try:
            driver.get(
                f'https://wein.konkuk.ac.kr/ptfol/imng/sbjtMngt/imng/findCulList.do?paginationInfo.currentPageNo={i}&subjSxnCd=0002&searchType=&searchValue=')
            dom = BeautifulSoup(driver.page_source, 'lxml')

            if dom.find(attrs={'class': 'NO_RESULT first last'}) != None:
                break
            else:
                for _ in dom.find_all('tr'):
                    table.append(_)
                i += 1
        except Exception:
            print(Exception)
    driver.close()
    sugang = {re.findall(r'href="#">(.+?)</a>', str(_))[0]: re.findall(r'</a></td><td> (.+?)</td>', str(_))[0] for _ in
              table if '심교' in str(_)}
    return sugang


if __name__ == '__main__':
    driver = get_driver()
    if login(driver) == True:
        print(std_info(driver))
        print(get_subj(driver))
