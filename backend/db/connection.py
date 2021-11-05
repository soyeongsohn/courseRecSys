import sqlalchemy

def db_conn(db_info):
    database_username = db_info['user']
    database_password = db_info['password']
    database_ip = db_info['host']
    database_name = db_info['db']
    database_connection = sqlalchemy.create_engine('mysql+pymysql://{0}:{1}@{2}/{3}'.
                                                   format(database_username, database_password,
                                                          database_ip, database_name))

    return database_connection
