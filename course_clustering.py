import pandas as pd
from konlpy.tag import Okt

# 파일 읽어오기
df = pd.read_pickle('./data/course_total.pkl')

# 학문분야 대분류 중복 제거 리스트
field = list(set(df['학문분야_대분류'].str.replace(' ', '').str.split(',').explode('학문분야_대분류')))
del field[0] # null값 (공백인 값) 제거

# 학문분야 분리해서 하나의 행으로 만들기
df = df.assign(학문분야_대분류=df['학문분야_대분류'].str.replace(' ', '').str.split(',')).explode('학문분야_대분류').reset_index(drop=True)


def tokenizing(data):
    """
    :param data: 명사를 추출할 단어의 리스트/pandas series
    :return: data에서 명사를 추출한 후 중복 단어 및 불용어를 제거한 리스트
    """
    okt = Okt()
    stopwords = ['가장' '가지', '학습', '이해', '대한', '주로', '따라서', '통해', '아래', '위해', '또한', '활용', '고자', '양문명']

    def extract_noun(sent):
        s = okt.pos(sent, norm=True, stem=True)
        nouns = [w[0] for w in s if (w[1] == 'Noun' and len(w[0]) > 1)]  # 두 글자 이상인 명사만 추출
        return nouns

    tokens = [word for word in (list(set(extract_noun(sent))) for sent in data) if not word in stopwords]

    return tokens