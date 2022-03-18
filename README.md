# Kuggle Project Team 4
## 건국대학교 교양 과목 추천 시스템(Recommendation system of elective courses in Konkuk university)
진행 기간: 2021.9.7 ~ 2021.11.30

### 아키텍쳐
![image](https://user-images.githubusercontent.com/60024018/159043939-5c47ebcd-3ef7-4edf-bc89-9121c74eac6b.png)

### 개발 프로세스
step 1. 데이터 수집 및 DB 구축
step 2. 데이터 전처리
step 3. 모델 구축
step 4. 웹 프로토타입 개발

#### 1. 데이터 수집 및 DB 구축
1\) 데이터 수집 - __동적/정적 크롤링__ 사용<br/>
심화 교양 정보(_./backend/crawling/course_crawling.py_) (<br/>
\- selenium과 BeautifulSoup를 이용하여 headless로 동적 크롤링 <br/>
\- 학교 요람 사이트(<a href="bulletins.konkuk.ac.kr">bulletins.konkuk.ac.kr</a>)의 심화 교양 교육 정보에서 데이터 수집 <br/>
\- 추가로 각 과목의 세부 페이지를 순회하며 과목 세부 정보 수집 <br/>
\- iframe과 csrf token때문에 정적 크롤링 사용에 실패함 <br/>
<br/>
에브리타임 리뷰(_./backend/crawling/review_crawling.py_) <br/>
\- requests의 Session을 이용한 정적 크롤링  <br/>
\- session에 로그인 쿠키 정보를 저장한 후 개발자도구의 Network의 Headers에서 request url 확인 후 사용 <br/>
\- 정적 크롤링과 비교해 크롤링 속도가 빨랐음 <br/>

2\) DB 구축 (_./backend/db/_) <br/>
\- 크롤링 데이터가 바로 DB에 저장되도록 구축 <br/>
\- 또한 서비스에서 사용자 정보를 받아오면 db에 저장하도록 테이블을 생성해놓음 <br/>

#### 2. 데이터 전처리 (_./backend/preprocessing/_)
1\) 과목 정보 <br/>
step 1. 대분류 결측치 처리 (_./course_classification.py_) <br/>
\- 정규표현식을 통한 전처리 <br/>
\- fasttext로 bi-gram 지도학습 진행 <br/>
step 2. 과목 해설 토큰화 (_./course_tokenizing.py_) <br/>
\- konlpy의 Mecab을 사용하여 명사만 추출한 후 토큰화 <br/>
\- fasttext pre-trained 모델을 불러와서 벡터화 <br/>
step 3. 코사인 유사도 산출 (_./course_tokenizing.py_) <br/>
\- 벡터화까지 끝마친 과목 해설을 바탕으로 코사인 유사도 계산 <br/>
\- numpy 배열로 형변환하여 element-wise 연산이 가능하게 함으로써 연산 속도를 높임 <br/>
\- 모델에 적용 시 로딩 속도를 빠르게 하기 위해서 파일로 저장 <br/>

2\) 에타 리뷰 <br/>
step 1. 리뷰 전처리 (_./review_pos_neg.py_) <br/>
\- 정규표현식을 통한 전처리 <br/>
step 2. 리뷰 토큰화 (_./review_pos_neg.py_) <br/>
\- konlpy의 Mecab을 사용하여 품사 태깅 후 조사와 같은 불필요한 품사는 제거한 후 bi-gram 산출 <br/>
step 3. 감성사전 구축 (_./review_pos_neg.py_) <br/>
\- Logistic Regression을 이용해 리뷰에서 가장 많이 사용된 단어를 긍정/부정 별로 150개 씩 산출 <br/>
step 4. 과목 별 긍부정 점수 산출 (_./review_sent_scoring.py_) <br/>
\- 전체 리뷰를 tf-idf matrix로 변환한 후 step 3에서 구축한 감성 사전을 활용하여 전체 리뷰에 대해 감성 점수 산출 <br/>
  감성점수 = (긍정 점수 - 부정 점수) / (긍정 점수 + 부정 점수) <br/>
step 5. 객관식 리뷰로 가중치 부여 (_./review_detailed_scoring.py_) <br/>
\- 각 범주 별로 0 ~ 5 사이의 숫자로 인코딩 <br/>
\- 학점 * 0.4 + 팀플 * 0.3 + 과제 * 0.2 + 시험 횟수 * 0.1 <br/>
** 가중치는 중요성을 임의로 판단하여 부여하였음 <br/>

#### 3. 모델 구축 (_./backend/model/_)
user의 정보로써 user의 심교 수강 내역을 사용함. (<a href="https://sugang.konkuk.ac.kr/">https://sugang.konkuk.ac.kr/</a>에서 가져옴)
- 과목 해설을 바탕으로 코사인 유사도 산출 후 합하여 정규화 + 심교 수강 내역의 학점을 숫자형으로 인코딩하여 가중치 부여 <br/>
  => 과목 유사도 점수를 바탕으로 상위 10개의 과목을 선정
- 에타 강의평을 바탕으로 감성 점수를 도출하고, 객관식 리뷰를 0 ~ 5 사이의 숫자형으로 인코딩하여 각 항목에 가중치를 부여, 최종 리뷰 점수 도출
  => 리뷰 점수를 바탕으로 상위 10개의 과목 중 4개의 과목을 선정
  
#### 4. 웹 프로토타입 개발 (_./frontend/_)
- flask를 사용하여 백엔드 구축
- html, css, js로 프론트엔드 구축

#### 돌아보니 아쉬운 점
- 크롤링 데이터로 db구축할 때 데이터프레임으로 저장 후 db로 쏘는 것이 아니라, 미리 테이블을 구축한 후 각 row들을 db로 쏘면 좋았을 것 같다.
- 과목 유사도 산출, 리뷰 점수 산출 과정에서 최신 모델을 사용하면 좋았을 것 같다. (리뷰 긍부정 점수 산출의 경우 BERT 기반의 모델을 사용했어도 좋았을 것 같다.)
- 추천 시스템 모델이 굉장히 단순하다. item의 유사도를 활용한 content-based filtering을 사용했는데, 사용자가 심교를 수강하지 않았을 경우 추천이 어렵다는 점에서
content-based filtering이 갖고 있는 "cold-start problem"이 없다는 장점을 잃었다. user profile을 더 잘 정의했어야 했다. 유사도 점수 산출 면도 조금 아쉽다.
- aws 서버에 프로토타입을 올리지 못했다. 처음에 성공했었는데 파일 하나가 빠져서 내리고 다시 올리는 과정에서 계속 오류가 났다. aws에 대해서 공부가 필요할 것 같다.

#### 그래도 잘한 점
- 데이터 수집부터 프로토타입 구축까지 모든 프로세스를 담당한 첫 프로젝트였다. 프로토타입 개발까지 무사히 끝마쳤다.
- 토큰화, 벡터화, 유사도 산출 등 자연어 처리의 일부를 직접 다뤄보았다.
