import logging

SERVER_NAME = 'localhost'
SERVER_PORT = 4020
DB_ENGINE = 'sqlite:///../websites.db'
DEBUG = True


if DEBUG:
    logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] (%(threadName)-10s) %(message)s', )

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(message)s')

