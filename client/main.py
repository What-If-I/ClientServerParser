from client import Client
from settings import SERVER_NAME, SERVER_PORT
from utils.html_parser import UrlParser

import logging

with Client(SERVER_NAME, SERVER_PORT, buffer_size=4096) as client:
    client.connect()

    while True:
        client.ask_for_task()
        server_response = client.receive_unpickled()

        url = server_response.pop('url', None)

        if url:
            logging.info("Got url: {url}".format(url=url))

            try:
                parsed_url = UrlParser(url)
            except ConnectionError:
                client.send_pickled({'Command': 'AbortTask'})
                continue
            else:
                url_title = parsed_url.get_title()
                url_links = parsed_url.get_links()

                data = {
                    "Task":
                        {
                            'url': url,
                            'title': url_title,
                            'links': url_links,
                        }
                }

                client.send_pickled(data)

        elif server_response.get("Command"):

            if server_response["Command"] == "Close":
                client.send_pickled({"Command": "Closed"})
                logging.debug("Got close command")
                break  # exit loop & close connection
