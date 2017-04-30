import asyncio
import logging

from protocol import BaseProtocol, Commands


class ClientProtocol(BaseProtocol):

    def connection_made(self, transport):
        self.transport = transport
        self.send(Commands.NEW_TASK)

    def connection_lost(self, exc):
        """
        Called when the connection is lost or closed.
        The argument is an exception object or None (the latter
        meaning a regular EOF is received or the connection was
        aborted or closed).
        """
        logging.debug("Connection lost! Closing client...")
        self.transport.close()
        loop = asyncio.get_event_loop()
        loop.stop()
