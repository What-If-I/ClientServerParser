import logging
import pickle
import threading
from socket import socket as Socket

from settings import server_name, server_port

logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s',
                    )

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(message)s')

urls = [
    "http://google.com", "http://youtube.com", "http://yandex.ru", "https://www.crummy.com/", "https://pymotw.com",
    "https://www.analyticsvidhya.com", "http://stackoverflow.com/",
]
# urls = [
#     "https://www.analyticsvidhya.com", "http://stackoverflow.com/",
# ]

parsed_urls = []
buff = bytes()


class Server:
    def __init__(self, address, port, max_connections):
        self.socket = Socket()
        self.address = address
        self.port = port
        self.connections = max_connections

    def start(self):
        logging.info('Starting server')
        self.socket.bind((self.address, self.port))
        self.socket.listen(self.connections)
        logging.info('Server has been started. Waiting for connections.')

    def close(self):
        self.socket.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.socket.__exit__(exc_type, exc_val, exc_tb)
        logging.info('Server closed')

    def accept(self):
        client_sock, client_addr = self.socket.accept()
        return client_sock, client_addr

    def receive(self, buffer_size):
        return self.socket.recv(buffer_size)

    def send(self, data, flags=0):
        return self.socket.send(data, flags)

    def receive_unpickled(self, buffer_size):
        return pickle.loads(self.receive(buffer_size))

    def send_pickled(self, data):
        return self.send(pickle.dumps(data))


class Client:
    def __init__(self, client_socket, client_address):
        self.socket = client_socket
        self.address = client_address

    def send(self, data, flags=0):
        return self.socket.send(data, flags)

    def receive(self, buff_size):
        return self.socket.recv(buff_size)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.debug('Exiting')
        self.socket.__exit__(exc_type, exc_val, exc_tb)

    def receive_unpickled(self, buffer_size):
        return pickle.loads(self.receive(buffer_size))

    def send_pickled(self, data):
        return self.send(pickle.dumps(data))

    def provide_client_tasks(self):
        logging.debug('Starting new thread')
        with self:
            while True:
                response = self.receive_unpickled(buffer_size=65536)
                logging.debug('Client response: {response}'.format(response=response))

                if response.get("Command"):

                    if response["Command"] == "NewTask" and urls:
                        logging.debug('Sending new task')

                        self.send_pickled(
                            {'url': urls.pop(), }
                        )

                    elif response["Command"] == "NewTask" and not urls:
                        logging.debug("No more urls left. Sending close command.")
                        self.send_pickled(
                            {"Command": "Close"}
                        )

                    elif response["Command"] == "Closed":
                        logging.debug("Got close command. Exiting.")
                        break

                elif response.get('Task'):
                    task = response['Task']

                    logging.debug("Got new task:" + str(response))
                    parsed_urls.append(task)

                    logging.debug("New parsed urls file" + str(parsed_urls))


with Server(server_name, server_port, max_connections=5) as server:
    server.start()

    while True:
        client = Client(*server.accept())
        threading.Thread(target=client.provide_client_tasks, args=()).start()
