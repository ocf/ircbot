import contextlib

import pymysql


@contextlib.contextmanager
def cursor(*, user='ocfircbot', password):
    conn: pymysql.connections.Connection = pymysql.connect(
        user=user,
        password=password,
        db='ocfircbot',
        host='mysql.ocf.berkeley.edu',
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4',
        autocommit=True,
    )
    try:
        with conn.cursor() as cursor:
            yield cursor
    finally:
        conn.close()
