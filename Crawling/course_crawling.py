from bs4 import BeautifulSoup
from selenium.webdriver import Chrome, ChromeOptions
import re
from time import sleep
import pandas as pd
import numpy as np
"""
This code is to get the information of advanced general education courses of Konkuk University on bulletins page.
https://bulletins.konkuk.ac.kr/
HTML source can be changed later.
"""

options = ChromeOptions()
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
options.add_argument("--incognito")
options.add_argument("headless")
driver = Chrome(options=options)

driver.get('https://bulletins.konkuk.ac.kr/ko-KR/CultureSearch/Culture/Advanced_Culture/')

# get the table for 2020
driver.find_element_by_xpath('/html/body/div[3]/div/div/div/div/div[2]/a[2]').click()
sleep(3) # wait for loading table

# create the dataframe to save the scraped data
course_2020 = pd.DataFrame(columns=['title_kor', 'title_eng', 'semester', 'cno', 'division', 'year',
                                    'credit', 'hour', 'dept', 'section', 'field_kor', 'field_eng'])

data_id = [] # will use it to get the details of each courses
while True:

    dom = BeautifulSoup(driver.page_source, 'lxml')
    # get the course info from the page source
    course = dom.select('body > div.container > div > div > div > div > div.col-md-12.columnBlockLayout > l.l2 > div > div.entity-grid.entitylist > div.view-grid.has-pagination > table > tbody > tr')
    for i in course:
        # get the data id
        data_id.append(re.findall(r'data-id="(.+?)"', str(i))[0])
        # it returns the list of all values of every columns of current data frame
        course_info = re.findall(r'data-value="(.+?)"', str(i))
        if len(course_2020.columns) > len(course_info):
            course_info.extend([np.nan, np.nan]) # fill with np.nan if blank
        course_2020.loc[len(course_2020)] = course_info
    if driver.find_elements_by_link_text('>')[1].get_attribute('aria-disabled') == 'true': # if reach the last page
        break
    # move to the next page
    driver.find_elements_by_link_text('>')[1].click() # 2020 -> index number is 1 (in 2021)
    sleep(3)


desc = [] # course description in Korean

# fields of study in the table in bulletins are same as field of study(sub category) on the detail page
field_L = [] # field of study(large category)
field_M = [] # field of study(medium category)
field_S = [] # field of study(small category)
profs = [] # prof name
codes = [] # code of substitution subject

for i in data_id:

    # move to the detail page
    driver.get(f'https://bulletins.konkuk.ac.kr/ko-KR/department/LIBERAL_ARTS/searchresultpage1/?id={i}')
    # wait for loading table
    sleep(1.5)
    dom = BeautifulSoup(driver.page_source, 'lxml')
    # get the course description
    desc.append(re.findall(r'>(.+?)</textarea>', str(dom.select('#new_description')[0]).replace('\r\n', ' '))[0])

    # get the code of substitution subject
    code = dom.find("label", {'id':'new_code_label'}).find_parent().find_next_sibling().find_next().text
    # it returns empty string if there's no code. so, just append.
    codes.append(code)

    # get the professors' name (can be single or multiple values, so get them as list)
    prof = dom.find_all('td', {'data-attribute':'new_professor'})
    # remove duplicated elements
    p = list((set([re.findall(r'data-value="(.+?)"', str(i))[0] for i in prof])))
    profs.append(p)

    # get the field of study
    fields = dom.select('#sub_part > div > div.view-grid > table > tbody > tr > td')
    l = list(set([i.attrs['aria-label'] for i in fields if i.attrs['data-th'] == '학문분야(대)']))
    m = list(set([i.attrs['aria-label'] for i in fields if i.attrs['data-th'] == '학문분야(중)']))
    s = list(set([i.attrs['aria-label'] for i in fields if i.attrs['data-th'] == '학문분야(소)']))
    field_L.append(l)
    field_M.append(m)
    field_S.append(s)



# add data in the data frame
course_2020['desc'] = desc
course_2020['field_L'] = field_L
course_2020['field_M'] = field_M
course_2020['field_S'] = field_S
course_2020['pname'] = profs
course_2020['subs_code'] = codes

# remove unnecessary columns
course_2020.drop(['title_eng', 'division', 'year', 'hour', 'dept', 'field_eng'], axis=1, inplace=True)


# save as pickle
course_2020.to_pickle('course_2020.pkl')

