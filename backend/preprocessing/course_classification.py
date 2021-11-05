import pandas as pd
import re
import fasttext


def preproc(df):
    """
    텍스트 전처리 함수
    df: 과목 정보 데이터 프레임
    """
    df = df.applymap(lambda x: re.sub(r'([.,?!])(\w)', '\g<1> \g<2>', x))  # 구두점 뒤에 문자가 있으면 공백 추가 -> .단어 => . 단어
    df = df.applymap(lambda x: re.sub(r'\s{2,}', '\n', x).strip())  # 공백이 2개 이상 반복되는 경우 하나만 남김 + strip -> 양쪽 공백 제거
    df = df.applymap(lambda x: re.sub(r'^\s[a-zA-Z가-힣]', '', x))  # 문장 시작이 공백인 경우 공백 삭제
    df = df.applymap(lambda x: x.replace('\n', ' '))  # 문장 중간 개행문자 제거
    df = df.applymap(lambda x: re.sub(r'[^\s\da-zA-Z가-힣.,?!:\'\"]', '', x))  # 공백, 한영, 숫자, 구두점을 제외한 나머지 글자 삭제 -> 특수문자 제거
    return df


def model(n=2, epoch=550):
    # df를 학문분야_대분류 유무로 train/test로 나눈 후 fasttext를 이용해 분류하기
    train = df.loc[df['학문분야'] != "", ['교과목해설', '학문분야']]
    test = df.loc[df['학문분야'] == "", ['교과목해설', '학문분야']]
    train['학문분야'] = train['학문분야'].apply(lambda _: "__label__" + _)
    train_path = "./data/labeled_train.txt"
    train.to_csv(train_path, sep="\t", index=False)

    # train data
    model = fasttext.train_supervised(train_path, wordNgrams=n, epoch=epoch, lr=0.3)

    # prediction
    pred = []
    for line in test['교과목해설']:
        pred_label = model.predict(line, threshold=0.5)[0]
        try:
            pred.append(pred_label[0])
        except IndexError:  # 예측하지 못한 값 처리
            pred.append("")

    # remove __label__ in predict data
    pred = list(map(lambda x: x.replace('__label__', ''), pred))

    df.loc[df['학문분야'] == "", '학문분야'] = pred

    return df


def course_classify(file_pth):
    """
    file_pth: dir path of pickle file of course info data
    """

    # load data
    df = pd.read_pickle(file_pth)

    # text preprocessing
    df = preproc(df)

    # multiple values -> single value, multiple rows
    df = df.assign(학문분야=df['학문분야'].str.split(',')).explode('학문분야').reset_index(drop=True)

    df = model()  # bi-gram

    df = model(n=1, epoch=50)  # uni-gram

    return df

if __name__ == "__main__":
    df = course_classify('./data/course_total.pkl')
    df.to_pickle('./data/course_fillna.pkl')