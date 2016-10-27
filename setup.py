from setuptools import setup


setup(
    name='ircbot',
    url='https://www.ocf.berkeley.edu/',
    author='Open Computing Facility',
    author_email='help@ocf.berkeley.edu',
    py_modules=['ircbot'],
    install_requires=[
        # Celery 3.1.19 has a bug with Redis UNIX sockets that breaks create:
        # https://github.com/celery/celery/issues/2903
        'celery[redis]<3.1.18',
        'irc',
        'ocflib',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
)
