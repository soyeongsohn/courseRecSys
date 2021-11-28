import pandas as pd
import re
from eunjeon import Mecab # 윈도우용
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from db.db_connection.connection import get_df


def exclude():
    # 불용어사전
    stopwords = pd.read_csv(
        "https://raw.githubusercontent.com/yoonkt200/FastCampusDataset/master/korean_stopwords.txt").values.tolist()
    stopwords = sum(stopwords, [])  # 2차원 리스트를 1차원 리스트로

    to_extract = ['교수', '님', '건대', '영화', '고', '으며', '나', '게', '면', '수', '은', '는', '이', '가']  # 나만의 불용어 추가

    stopwords += to_extract  # 합치기

    remove_pos = ['IC', 'JKS', 'JKC', 'JKG', 'JKO', 'JKB', 'JKV', 'JKQ', 'JX', 'JC',
                  'XPN', 'XSN', 'XSV', 'XSA', 'XR', 'SF', 'SE', 'SS', 'SP', 'SO', 'SW']
    # 제거품사 = 감탄사. 조사, 접두사/접미사, 부호
    # 추가 : 연결어미 (EC)

    return stopwords, remove_pos


def tokenizing(data):
    m = Mecab()
    words = m.pos(data)
    stopwords, remove_pos = exclude()
    words = [word for word,tag in words if tag not in remove_pos and word not in stopwords]
    return words


def cleaning(text):
    hangul = re.compile('[^ 가-힣]')  # 한글 추출(ㅋㅋㅋ 등 제외)
    result = hangul.sub('', text)  # 한글과 띄어쓰기를 제외한 모든 부분을 제거
    result = re.sub(' +',' ', result) # 띄어쓰기 2개 이상이면 1개로
    return result


def clean_df():
    df = get_df('review')
    df.avg_rate = df.avg_rate.astype(int)
    df.review = df.review.apply(cleaning)
    return df


# 긍정에 1, 부정에 0
def rating_to_label(rating):
    if rating > 3:
        return 1  # 긍정
    else:
        return 0  # 부정


def concat(df):
    result = df.loc[df.avg_rate != 3]
    result.reset_index(drop=True, inplace=True)
    result = result.assign(y=result.avg_rate.apply(rating_to_label))
    # result 의 리뷰 전체 코퍼스
    review_total = list(result.review)
    return review_total, result


def posneg():
    review_total, result = concat()
    vectorizer = CountVectorizer(tokenizer=tokenizing, ngram_range=(2, 2))
    train_x = vectorizer.fit_transform(review_total)
    train_label = result['y']
    classifier = LogisticRegression()
    classifier.fit(train_x, train_label)

    idxs_coef = list(enumerate(classifier.coef_[0]))
    positive_idxs = sorted(idxs_coef, key=lambda x: -x[1])[:150]
    negative_idxs = sorted(idxs_coef, key=lambda x: x[1])[:150]  # 긍부정 단어 150개

    vocab2idx = vectorizer.vocabulary_

    neg = []
    for index, v in negative_idxs:
        for key, value in vocab2idx.items():
            if index == value:
                neg.append(key)
    pos = []
    for index, v in positive_idxs:
        for key, value in vocab2idx.items():
            if index == value:
                pos.append(key)

    return pos, neg


if __name__ == "__main__":
    posneg() # 이후 단어 선별/추가 후작업 후 pickle 파일로 저장함(py파일에는 따로 추가하지 않음)

