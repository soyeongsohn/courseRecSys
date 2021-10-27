import pandas as pd

# 파일 불러오기
course_2019 = pd.read_pickle('./data/course_2019.pkl')
course_2020 = pd.read_pickle('./data/course_2020.pkl')
course_2021 = pd.read_pickle('./data/course_2021.pkl')

# 파일 합치기
course = pd.concat([course_2019, course_2020, course_2021], ignore_index=True)

# 교수명 비어있는 교과목 삭제
to_drop = [i for i in range(len(course)) if course['교수명'][i] == '']

course.drop(to_drop, axis=0, inplace=True)

# 교수명 하나 당 한 행으로 쪼개기
course = course.assign(교수명=course['교수명'].str.split(',')).explode('교수명').reset_index(drop=True)

# 중복 삭제
course.drop_duplicates(subset=['학수번호', '교수명'], inplace=True)

# 인덱스 초기화
course.reset_index(drop=True, inplace=True)

# pickle로 저장
course.to_pickle('./data/course_total.pkl')

