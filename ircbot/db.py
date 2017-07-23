import contextlib

import pymysql


@contextlib.contextmanager
def cursor(*, user='ocfircbot', password):
    with contextlib.closing(pymysql.connect(
        user=user,
        password=password,
        db='ocfircbot',
        host='mysql.ocf.berkeley.edu',
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4',
        autocommit=True,
    )) as conn:
        with conn as cursor:
            yield cursor
