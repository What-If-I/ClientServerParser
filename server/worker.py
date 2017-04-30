import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import WebSites, Links, DB_ENGINE
from protocol import Commands, Task, BaseWorker

engine = create_engine(DB_ENGINE, echo=False)
Session = sessionmaker(engine)

session = Session()
urls_to_parse = [url.url for url in session.query(WebSites.url).filter(WebSites.parsed != True).all()]


class TaskProvider(BaseWorker):
    def __init__(self):
        self.latest_url = None
        self.last_url_parsed = True
        self.db_session = Session()

    def _exit(self):
        if not self.last_url_parsed:
            self._task_failed(self.latest_url)

    def _task_failed(self, url):
        logging.info(f"Failed to pars {url}")
        self._url_back_to_q(url)

    @staticmethod
    def _url_back_to_q(url):
        urls_to_parse.append(url)
        logging.debug(f'{url} returned to queue.')

    @staticmethod
    def _get_new_url():
        return urls_to_parse.pop()

    def _save_parsed_urls(self, task: Task):
        website = self.db_session.query(WebSites).filter_by(url=task.url).first()
        website.title = task.title
        website.parsed = True

        for link in task.links:
            new_link = Links(site_id=website.id, link=link)
            self.db_session.add(new_link)

        self.db_session.commit()

    def process_data(self, request: Commands or Task):
        response = None
        try:
            logging.debug('Client response: {response}'.format(response=request))

            if request in Commands:
                if request is Commands.NEW_TASK and urls_to_parse:

                    if not self.last_url_parsed:
                        self._task_failed(self.latest_url)

                    self.latest_url = self._get_new_url()
                    logging.debug('Sending new task')

                    response = Task(self.latest_url, '', [])

                    self.last_url_parsed = False

                elif request is Commands.NEW_TASK and not urls_to_parse:
                    response = Commands.CLOSE
                    logging.debug("No more urls left. Sending close command.")

                elif request is Commands.CLOSE:
                    logging.debug("Got close command. Exiting.")

                elif request is Commands.ABORT_TASK:
                    self.last_url_parsed = True
                    logging.debug(f"Got Abort command. Task: {self.latest_url} aborted.")

            # TODO: переделать определение таска
            elif isinstance(request, Task):
                logging.debug("Got new task:" + str(request))
                self._save_parsed_urls(request)
                self.last_url_parsed = True

                if urls_to_parse:
                    self.latest_url = self._get_new_url()
                    response = Task(self.latest_url, '', [])
                else:
                    response = Commands.CLOSE

        except Exception:
            logging.exception("Ooops: ")

        finally:
            return response
