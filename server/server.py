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

urls = ["http://google.com", "http://youtube.com", "http://yandex.ru", "https://www.crummy.com/", "https://pymotw.com",
        "https://www.analyticsvidhya.com", "http://stackoverflow.com/", ]

parsed_urls = []


class Server:
    def __init__(self, address, port, max_connections):
        self.socket = Socket()
        self.address = address
        self.port = port
        self.connections = max_connections

    def start(self):
        logging.info('Starting server')
        try:
            self.socket.bind((self.address, self.port))
        except OSError:
            logging.debug("Address already taken - {address}:{port}".format(address=self.address, port=self.port))
            exit(1)
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


class Client:
    def __init__(self, client_socket, client_address, buffer_size):
        self.socket = client_socket
        self.address = client_address
        self.buffer_size = buffer_size
        self.latest_url = None
        self.last_url_parsed = True

    def send(self, payload, flags=0):
        """
        Send message(payload) to socket. Appends 8 bytes with information of message length to the beginning.
        """
        total_sent = 0
        send_bytes = len(payload).to_bytes(8, byteorder='little') + payload

        while total_sent < len(send_bytes):
            try:
                sent = self.socket.send(send_bytes[total_sent:])
            except ConnectionResetError:
                logging.warning("Connection aborted.")
                logging.exception("Exception:")
                exit(1)
            if sent == 0:
                raise RuntimeError("Connection broken")
            total_sent += sent

    def receive(self):
        """
        Receive data by chunks of buffer size.
        :return: full message without leading 8 bytes (message length)
        """
        message = self.socket.recv(self.buffer_size)

        if len(message) < self.buffer_size:
            return message[8:]  # First 8 bytes contains payload length

        else:
            chunks = []
            payload_size, payload = int.from_bytes(message[0:8], byteorder='little'), message[8:]
            chunks.append(payload)
            bytes_received = len(payload)

            while bytes_received < payload_size:
                chunk = self.socket.recv(min(payload_size - bytes_received, self.buffer_size))
                if chunk == b'':
                    raise RuntimeError("Socket connection broken")
                chunks.append(chunk)
                bytes_received += len(chunk)

            return b''.join(chunks)

    @staticmethod
    def url_back_to_q(url):
        urls.append(url)
        logging.debug('{url} returned to queue.'.format(url=url))

    def _task_failed(self, url):
        logging.info("Failed to pars {url}".format(url=url))
        self.url_back_to_q(url)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.debug('Exiting')
        self.socket.__exit__(exc_type, exc_val, exc_tb)
        if not self.last_url_parsed:
            self._task_failed(self.latest_url)

    def receive_unpickled(self):
        return pickle.loads(self.receive())

    def send_pickled(self, data):
        return self.send(payload=pickle.dumps(data))

    @staticmethod
    def get_new_url():
        return urls.pop()

    @staticmethod
    def save_parsed_urls(task):
        parsed_urls.append(task)

    def provide_client_tasks(self):
        logging.debug('Starting new thread')

        with self:
            while True:
                response = self.receive_unpickled()
                logging.debug('Client response: {response}'.format(response=response))

                if response.get("Command"):
                    if response["Command"] == "NewTask" and urls:

                        if not self.last_url_parsed:
                            self._task_failed(self.latest_url)

                        self.latest_url = self.get_new_url()
                        logging.debug('Sending new task')

                        self.send_pickled(
                            {'url': self.latest_url, }
                        )

                        self.last_url_parsed = False

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
                    self.save_parsed_urls(task)
                    self.last_url_parsed = True
