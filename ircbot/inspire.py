from ircbot import db


def inspire(mysql_password, msg):
    search = msg.strip().split(' ')
    term = ' '.join(search[1:]) if len(search) > 1 else ''

    with db.cursor(password=mysql_password) as c:
        c.execute(
            'SELECT text FROM `inspire` ' +
            'WHERE LOWER(text) LIKE LOWER(%s) ' +
            'ORDER BY RAND() LIMIT 1',
            '%{}%'.format(term),
        )

        return c.fetchone()['text']
