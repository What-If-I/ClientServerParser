from server import Server, Client
from settings import server_name, server_port, db_engine, DEBUG

from threading import Thread

from database import WebSites, Links
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import logging

if DEBUG:
    logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] (%(threadName)-10s) %(message)s', )

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(message)s')

engine = create_engine(db_engine, echo=False)
Session = sessionmaker(engine)

session = Session()
urls_to_parse = [url.url for url in session.query(WebSites.url).filter(WebSites.parsed != True).all()]


class TaskProvider:
    def __init__(self, client):
        logging.debug('Starting new thread')

        self.client = client
        self.latest_url = None
        self.last_url_parsed = True
        self.db_session = Session()

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
        urls_to_parse.append(url)
        logging.debug('{url} returned to queue.'.format(url=url))

    @staticmethod
    def get_new_url():
        return urls_to_parse.pop()

    def save_parsed_urls(self, task):
        website = self.db_session.query(WebSites).filter_by(url=task['url']).first()
        website.title = task['title']
        website.parsed = True

        for link in task['links']:
            new_link = Links(site_id=website.id, link=link)
            self.db_session.add(new_link)

        self.db_session.commit()

    def provide_tasks(self):
        with self:
            while True:
                response = self.client.receive_unpickled()
                logging.debug('Client response: {response}'.format(response=response))

                if response.get("Command"):
                    if response["Command"] == "NewTask" and urls_to_parse:

                        if not self.last_url_parsed:
                            self._task_failed(self.latest_url)

                        self.latest_url = self.get_new_url()
                        logging.debug('Sending new task')

                        self.client.send_pickled(
                            {'url': self.latest_url, }
                        )

                        self.last_url_parsed = False

                    elif response["Command"] == "NewTask" and not urls_to_parse:
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

    while urls_to_parse:
        client = Client(*server.accept(), buffer_size=4096)
        Thread(target=TaskProvider(client).provide_tasks).start()

    logging.info("No urls left.")
