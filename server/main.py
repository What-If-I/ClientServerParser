from server import Server, Client
from settings import server_name, server_port
from threading import Thread

with Server(server_name, server_port, max_connections=5) as server:
    server.start()

    while True:
        client = Client(*server.accept(), buffer_size=4096)
        Thread(target=client.provide_client_tasks).start()
