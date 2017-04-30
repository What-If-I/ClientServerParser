import logging

from client.utils.html_parser import UrlParser
from protocol import BaseWorker, Task, Commands


class TaskHandler(BaseWorker):

    def process_data(self, request: Task or Commands):

        response = None

        if isinstance(request, Task):
            task = request
            logging.info("Got url: {url}".format(url=task.url))

            try:
                url_parser = UrlParser(task.url)
            except ConnectionError:
                response = Commands.ABORT_TASK
            else:
                task.title = url_parser.get_title()
                task.links = url_parser.get_links()
                response = task

        elif request in Commands:

            if request is Commands.CLOSE:
                logging.debug("Got close command")
                response = Commands.CLOSE

        return response
