import re
import fasttext
import sqlalchemy
from db.db_connection.connection import db_conn, sql_conn, get_df


def preproc(df):
    """
    텍스트 전처리 함수
    df: 과목 정보 데이터 프레임
    """
    df.description = df.description.apply(lambda x: re.sub(r'^\s[a-zA-Z가-힣]', '', x))  # 문장 시작이 공백인 경우 공백 삭제
    df.description = df.description.apply(
        lambda x: re.sub(r'([.,?!])(\w)', '\g<1> \g<2>', x))  # 구두점 뒤에 문자가 있으면 공백 추가 -> .단어 => . 단어
    df.description = df.description.apply(
        lambda x: re.sub(r'[^\s\da-zA-Z가-힣.,?!:\'\"]', ' ', x))  # 공백, 한영, 숫자, 구두점을 제외한 나머지 글자 삭제 -> 특수문자 제거
    df.description = df.description.apply(
        lambda x: re.sub(r'\s{2,}', '\n', x).strip())  # 공백이 2개 이상 반복되는 경우 하나만 남김 + strip -> 양쪽 공백 제거
    df.description = df.description.apply(lambda x: x.replace('\n', ' '))  # 문장 중간 개행문자 제거
    return df


def model(df, n=2, epoch=1500):
    # df를 학문분야_대분류 유무로 train/test로 나눈 후 FastText를 이용해 분류하기
    train = df.loc[df['field'] != "", ['description', 'field']]
    test = df.loc[df['field'] == "", ['description', 'field']]
    train['field'] = train['field'].apply(lambda _: "__label__" + _)
    train_path = "./data/labeled_train.txt"
    train.to_csv(train_path, sep="\t", index=False)

    # train data
    model = fasttext.train_supervised(train_path, wordNgrams=n, epoch=epoch, lr=0.3)

    # prediction
    pred = []
    for line in test['description']:
        pred_label = model.predict(line, threshold=0.5)[0]
        try:
            pred.append(pred_label[0])
        except IndexError:  # 예측하지 못한 값 처리
            pred.append("")

    # remove __label__ in predict data
    pred = list(map(lambda x: x.replace('__label__', ''), pred))

    df.loc[df['field'] == "", 'field'] = pred

    return df


def course_classify():
    # load data
    df = get_df('course_total')
    # text preprocessing
    df = preproc(df)

    # multiple values -> single value, multiple rows
    df = df.assign(field=df['field'].str.replace(' ', '').str.split(',')).explode('field').reset_index(drop=True)

    df = model(df)  # bi-gram

    # 남아있는 결측치 (1개) 채우기
    df.loc[df.field == '', 'field'] = '사회과학'  # 명화를통한인간의이해

    return df


def load_to_db():
    database_connection = db_conn()
    conn, curs = sql_conn()
    df.to_sql(con=database_connection, name='course_fillna', if_exists='replace', index=False,
              dtype={'courseno': sqlalchemy.sql.sqltypes.CHAR(9), 'credit': sqlalchemy.types.INTEGER(),
                     'domain': sqlalchemy.sql.sqltypes.VARCHAR(12),
                     'profname': sqlalchemy.sql.sqltypes.VARCHAR(10),
                     'field': sqlalchemy.sql.sqltypes.VARCHAR(5)})
    sql = """alter table course_fillna add PRIMARY KEY (courseno, profname, field);"""
    curs.execute(sql)
    conn.commit()

    df.to_pickle('./data/course_fillna.pkl')  # save backup just in case

    curs.close()
    conn.close()


if __name__ == "__main__":
    df = course_classify()
    load_to_db()
