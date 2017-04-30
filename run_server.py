import asyncio

import logging

from protocol import BaseProtocol
from server.settings import SERVER_NAME, SERVER_PORT
from server.worker import TaskProvider

loop = asyncio.get_event_loop()
coro = loop.create_server(lambda: BaseProtocol(TaskProvider), host=SERVER_NAME, port=SERVER_PORT)
server = loop.run_until_complete(coro)

print('Serving on {}'.format(server.sockets[0].getsockname()))
try:
    loop.run_forever()
except KeyboardInterrupt:
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()

logging.info("No urls left.")
