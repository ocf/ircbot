from ircbot import db


def rand(mysql_password):
    with db.cursor(password=mysql_password) as c:
        c.execute(
            'SELECT text FROM inspire ORDER BY RAND() LIMIT 1',
        )

        return c.fetchone()['text']


def like(mysql_password, term):
    with db.cursor(password=mysql_password) as c:
        c.execute(
            'SELECT text FROM inspire WHERE LOWER(text) LIKE LOWER(%s) ORDER BY RAND() LIMIT 1',
            '%{}%'.format(term),
        )
        result = c.fetchone()
        if result is None:
            return "No quotes matching '{}' found.".format(term)
        else:
            return result['text']
