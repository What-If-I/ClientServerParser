import logging
import pickle
from socket import socket as Socket


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
        message = ""
        try:
            message = self.socket.recv(self.buffer_size)
        except ConnectionResetError:
            logging.warning("Connection aborted.")
            logging.exception("Exception: ")
            exit(1)

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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.debug('Exiting')
        self.socket.__exit__(exc_type, exc_val, exc_tb)

    def receive_unpickled(self):
        return pickle.loads(self.receive())

    def send_pickled(self, data):
        return self.send(payload=pickle.dumps(data))
