from bs4 import BeautifulSoup
from selenium.webdriver import Chrome, ChromeOptions
import re
from time import sleep
import pandas as pd
import numpy as np

def get_driver():
    options = ChromeOptions()
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    options.add_argument("--incognito")
    options.add_argument("headless")
    global driver
    driver = Chrome(options=options)

def get_course(year):
    global course
    
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
    data_id = [] # 추후 과목 세부 정보 페이지 이동하기 위함
    while True:
        sleep(5)
        # 다음 페이지로 이동
        dom = BeautifulSoup(driver.page_source, 'lxml')

        course = dom.select(f'body > div.container > div > div > div > div > div.col-md-12.columnBlockLayout > l.l{no} > div > div.entity-grid.entitylist > div.view-grid.has-pagination > table > tbody > tr')
        for i in course:
            data_id.append(re.findall(r'data-id="(.+?)"', str(i))[0])
            course_info = re.findall(r'data-value="(.+?)"', str(i))
            col = re.findall(r'data-th="(.+?)"', str(course))
            cols = [i for n, i in enumerate(col) if i not in col[:n]]
            if len(cols)-1 > len(course_info):
                course_info.extend([np.nan, np.nan]) # 학문분야가 공백인 경우 nan 값으로 채우기(한, 영 이므로 2개)
            courses.append(course_info)
            
        if driver.find_elements_by_link_text('>')[no-1].get_attribute('aria-disabled') == 'true': # 마지막 페이지에 도달한 경우
            break
        driver.find_elements_by_link_text('>')[no-1].click()
        
    course = pd.DataFrame(courses, columns=['교과목명', '영문과목명', '개설학기', '학수번호', '이수구분', '학년', 
                                    '학점', '시간', '학과', '영역', '학문분야', '영문학문분야'])
    return data_id
    
def get_details(data_id):
    
    # 새로 추가할 열 추가
    global course
    course = course.reindex(columns = course.columns.tolist() + ['교과목해설', '교수명', '학문분야_대분류', '과목대체코드'])
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
                
        course.loc[i, '교과목해설'] = desc
        code = dom.find("label", {'id':'new_code_label'}).find_parent().find_next_sibling().find_next().text
        # 동일 과목 대체 코드가 없으면 빈 문자열을 리턴하므로 대체 코드 유무에 관계없이 append

        course.loc[i, '과목대체코드'] = code

        prof = dom.find_all('td', {'data-attribute':'new_professor'})
        p = list((set([re.findall(r'data-value="(.+?)"', str(_))[0] for _ in prof])))

        course.loc[i, '교수명'] = (', ').join(p)


        fields = dom.select('#sub_part > div > div.view-grid > table > tbody > tr > td')
        l = list(set([_.attrs['aria-label'] for _ in fields if _.attrs['data-th'] == '학문분야(대)']))

        course.loc[i, '학문분야_대분류'] = (', ').join(l)

def main(year):
    global course
    data_id = get_course(year)
    get_details(data_id)   
    driver.close()
    course.drop(['영문과목명', '이수구분', '학년', '시간', '학과', '학문분야', '영문학문분야'], axis=1, inplace=True)
    course.to_pickle(f'./data/course_{year}.pkl')

if __name__ == "__main__":
    years = [2019, 2020, 2021]
    for year in years:
        main(year)
