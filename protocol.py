import asyncio
import pickle
from enum import auto, IntEnum
from typing import Type


class Commands(IntEnum):
    START = auto()
    STOP = auto()
    CLOSE = auto()
    NEW_TASK = auto()
    ABORT_TASK = auto()


class Task:
    url = ''
    title = ''
    links = []

    def __init__(self, url: str, title: str, links: list):
        self.url = url
        self.title = title
        self.links = links

    def __str__(self):
        cls_name = self.__class__.__name__
        return f"({cls_name}):\n{self.title} - {self.url}\n{self.links}"


class BaseWorker:

    def process_data(self, data: Task or Commands):
        raise NotImplementedError


class BaseProtocol(asyncio.Protocol):

    def __init__(self, worker: Type[BaseWorker]):
        self.worker = worker()
        self.transport = None

    def send(self, payload):
        """
        Send message(payload) to socket. 
        """
        payload = pickle.dumps(payload)
        self.transport.write(payload)

    def connection_made(self, transport):
        """
        Called when a connection is made.
        The argument is the transport representing the pipe connection.
        To receive data, wait for data_received() calls.
        When the connection is closed, connection_lost() is called.
        """
        self.transport = transport

    def data_received(self, data):
        """
        Called when some data is received.
        The argument is a bytes object.
        """
        data = (pickle.loads(data))
        response = self.worker.process_data(data)
        if response:
            self.send(response)
        else:
            self.transport.close()

    def connection_lost(self, exc):
        """
        Called when the connection is lost or closed.
        The argument is an exception object or None (the latter
        meaning a regular EOF is received or the connection was
        aborted or closed).
        """
        print("Connection lost! Closing server...")
        self.transport.close()


def protocol_factory(worker, func):
    return lambda: func(worker)

