from client import Client
from settings import server_name, server_port
from utils.html_parser import UrlParser

import logging

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(message)s',
                    )

with Client(server_name, server_port, buffer_size=4096) as client:
    client.connect()

    while True:
        client.ask_for_task()
        server_response = client.receive_unpickled()

        url = server_response.pop('url', None)

        if url:
            logging.info("Got url: {url}".format(url=url))

            parsed_url = UrlParser(url)
            url_title = parsed_url.get_title()
            url_links = parsed_url.get_links()

            data = {
                "Task":
                    {
                        'Url': url,
                        'Title': url_title,
                        'Links': url_links,
                    }
            }

            client.send_pickled(data)

        elif server_response.get("Command"):

            if server_response["Command"] == "Close":
                client.send_pickled({"Command": "Closed"})
                logging.debug("Sent Close command")
                break  # exit loop & close connection
