import logging
import pickle
from socket import socket as Socket

from settings import server_name, server_port
from utils.html_parser import UrlParser

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(message)s',
                    )

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(message)s')


def unpickle_response(response):
    return pickle.loads(response)


def ask_for_task(socket):
    return socket.sendall(pickle.dumps({'new_task': True}))


def get_response_from(socket):
    return socket.recv(2048)


class Client:
    def __init__(self, address, port):
        self.socket = Socket()
        self.address = address
        self.port = port

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.socket.__exit__()
        logging.info('Client closed')

    def connect(self):
        logging.info('Starting client')
        self.socket.connect((self.address, self.port))

    def send(self, data, flags=0):
        return self.socket.send(data, flags)

    def receive(self, buffer_size):
        return self.socket.recv(buffer_size)

    def ask_for_task(self):
        return self.send_pickled({'Command': "NewTask"})

    def receive_unpickled(self):
        return pickle.loads(self.receive(2048))

    def send_pickled(self, data):
        return self.send(pickle.dumps(data))


with Client(server_name, server_port) as client:
    client.connect()
    logging.info('Connected to {server}:{port}'.format(server=client.address, port=client.port))
    while True:
        client.ask_for_task()
        server_response = client.receive_unpickled()

        url = server_response.pop('url', None)

        if url:
            logging.debug("Got url: {url}".format(url=url))

            parsed_url = UrlParser(url)
            url_title = parsed_url.get_title()
            url_links = parsed_url.get_links()

            data = {
                "Task":
                    {
                        'Url': url,
                        'Title': url_title,
                        'Links': url_links,
                    }
            }

            client.send_pickled(data)

        elif server_response.get("Command"):

            if server_response["Command"] == "Close":
                client.send_pickled({"Command": "Closed"})
                logging.debug("Sent Close command")
                break  # exit loop & close connection
