import asyncio

import logging

from client.protocol import ClientProtocol
from client.worker import TaskHandler
from client.settings import SERVER_NAME, SERVER_PORT

loop = asyncio.get_event_loop()
coro = loop.create_connection(lambda: ClientProtocol(TaskHandler), host=SERVER_NAME, port=SERVER_PORT)
client = loop.run_until_complete(coro)

print('Serving on {}'.format(client[0]._extra['sockname']))
try:
    loop.run_forever()
except KeyboardInterrupt:
    client.close()
    loop.run_until_complete(client.wait_closed())
    loop.close()

logging.info("No urls left.")
