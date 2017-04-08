import logging

SERVER_NAME = 'localhost'
SERVER_PORT = 4020
DEBUG = False

if DEBUG:
    logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s', )

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s', )