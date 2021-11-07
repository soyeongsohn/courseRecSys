import re
from konlpy.tag import Mecab
from gensim import models
from sklearn.metrics.pairwise import cosine_similarity
import pickle
from db.db_connection.connection import get_df


def tokenizing(data):
    mecab = Mecab()
    stopwords = ['가장' '가지', '학습', '이해', '대한', '주로', '따라서', '통해', '아래', '위해', '또한', '활용', '고자', '양문명']

    def extract_noun(sent):
        sent = re.sub(r'[^\s\da-zA-Z가-힣]', ' ', sent)  # 숫자, 공백, 문자 외 제거
        sent = re.sub(r'\s{2,}', '\n', sent).strip()  # 공백이 2개 이상 반복되는 경우 하나만 남김
        nouns = mecab.nouns(sent)

        return nouns

    tokens = [[word for word in (extract_noun(sent)) if not word in stopwords and len(word) > 1] for sent in data]

    return tokens


def vectorized():
    # 데이터프레임 불러오기
    df = get_df('course_fillna')

    # tokenizing
    token = tokenizing(df['description'])
    # pre-trained FastText 모델 load
    ko_model = models.fasttext.load_facebook_model("D:/정리/cc.ko.300.bin.gz")

    # 벡터로 변환

    c2vec = []
    for t in token:
        wvec = 0
        for w in t:
            wvec += ko_model.wv.word_vec(w)

        c2vec.append(wvec / len(t))  # 토큰의 길이로 나눠서 정규화

    # 코사인 유사도 계산
    cos_sim = cosine_similarity(c2vec, c2vec)

    # 빠른 로딩 위해 matrix 저장
    with open("cos_sim.txt", "wb") as f:
        pickle.dump(cos_sim, f)


if __name__ == "__main__":
    vectorized()  # 코사인 유사도 계산 후 파일로 저장