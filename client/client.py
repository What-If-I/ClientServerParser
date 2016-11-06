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


class Client:
    def __init__(self, address, port, buffer_size):
        self.socket = Socket()
        self.address = address
        self.port = port
        self.buffer_size = buffer_size

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.socket.__exit__()
        logging.info('Client closed')

    def connect(self):
        logging.info('Starting client')
        self.socket.connect((self.address, self.port))

    def send(self, payload, flags=0):
        total_sent = 0
        send_bytes = len(payload).to_bytes(8, byteorder='little') + payload

        while total_sent < len(send_bytes):
            sent = self.socket.send(send_bytes[total_sent:])
            if sent == 0:
                raise RuntimeError("Socket connection broken")
            total_sent += sent

    def receive(self):
        message = self.socket.recv(self.buffer_size)

        if len(message) < self.buffer_size:
            return message[8:]  # First 8 bytes contains payload size

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

    def ask_for_task(self):
        return self.send_pickled({'Command': "NewTask"})

    def receive_unpickled(self):
        return pickle.loads(self.receive())

    def send_pickled(self, bytes):
        return self.send(pickle.dumps(bytes))


with Client(server_name, server_port, buffer_size=4096) as client:
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
