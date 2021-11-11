from db.db_connection.connection import sql_conn


conn, curs = sql_conn()

drop_sql = "DROP TABLE IF EXISTS std_info"
curs.execute(drop_sql)
conn.commit()

sql = """CREATE TABLE std_info (
        stdno INT,
        dept VARCHAR(20) NOT NULL,
        title VARCHAR(20),
        courseno CHAR(9),
        grade FLOAT,
        enter_date DATETIME DEFAULT now() on update now(),
        PRIMARY KEY(stdno, title),
        CHECK (grade >= 0.0 AND grade <= 4.5)
        );""" # 같은 학생이 동일 과목을 들을 수 없기 때문에 두 개를 묶어서 기본키로 지정

curs.execute(sql)