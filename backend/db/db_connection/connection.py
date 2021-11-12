import sqlalchemy
from pathlib import Path
import json
import pandas as pd
import pymysql
import os


def get_db_info():
    dirpath = Path(__file__).parents[3]
    with open(os.path.join(dirpath, "db_private.json")) as f:
        db_info = json.load(f)

    return db_info


def sql_conn():
    db_info = get_db_info()
    conn = pymysql.connect(host=db_info['host'], user=db_info['user'], password=db_info['password'], db=db_info['db_connection'])
    curs = conn.cursor(pymysql.cursors.DictCursor)
    return conn, curs


def db_conn():
    db_info = get_db_info()
    database_username = db_info['user']
    database_password = db_info['password']
    database_ip = db_info['host']
    database_name = db_info['db_connection']
    database_connection = sqlalchemy.create_engine('mysql+pymysql://{0}:{1}@{2}/{3}'.
                                                   format(database_username, database_password,
                                                          database_ip, database_name))

    return database_connection


def get_df(tablename):
    conn, _ = sql_conn()
    sql = f"SELECT * from {tablename}"
    df = pd.read_sql(sql, conn)

    if tablename != 'review':
        df.credit = df.credit.astype(str)

    conn.close()
    return df

