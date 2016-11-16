from server import Server, Client
from settings import server_name, server_port
from threading import Thread

import logging

urls = ["http://google.com", "http://youtube.com", "http://yandex.ru", "https://www.crummy.com/", "https://pymotw.com",
        "https://www.analyticsvidhya.com", "http://stackoverflow.com/", ]

parsed_urls = []


class TaskProvider:
    def __init__(self, client):
        self.client = client
        self.latest_url = None
        self.last_url_parsed = True

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.client.__exit__(*args, **kwargs)
        if not self.last_url_parsed:
            self._task_failed(self.latest_url)

    def _task_failed(self, url):
        logging.info("Failed to pars {url}".format(url=url))
        self.url_back_to_q(url)

    @staticmethod
    def url_back_to_q(url):
        urls.append(url)
        logging.debug('{url} returned to queue.'.format(url=url))

    @staticmethod
    def get_new_url():
        return urls.pop()

    @staticmethod
    def save_parsed_urls(task):
        parsed_urls.append(task)

    def provide_tasks(self):
        logging.debug('Starting new thread')

        with self:
            while True:
                response = self.client.receive_unpickled()
                logging.debug('Client response: {response}'.format(response=response))

                if response.get("Command"):
                    if response["Command"] == "NewTask" and urls:

                        if not self.last_url_parsed:
                            self._task_failed(self.latest_url)

                        self.latest_url = self.get_new_url()
                        logging.debug('Sending new task')

                        self.client.send_pickled(
                            {'url': self.latest_url, }
                        )

                        self.last_url_parsed = False

                    elif response["Command"] == "NewTask" and not urls:
                        logging.debug("No more urls left. Sending close command.")
                        self.client.send_pickled(
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


with Server(server_name, server_port, max_connections=5) as server:
    server.start()

    while True:
        client = Client(*server.accept(), buffer_size=4096)
        Thread(target=TaskProvider(client).provide_tasks).start()
