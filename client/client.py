import logging
import pickle
from socket import socket as Socket


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
        try:
            self.socket.connect((self.address, self.port))
            logging.info('Connected to {server}:{port}'.format(server=self.address, port=self.port))
        except ConnectionRefusedError:
            logging.warning('Failed to connect.')
            logging.exception('Exception: ')
            exit(1)

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
