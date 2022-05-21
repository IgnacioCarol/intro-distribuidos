import socket
import threading
from typing import List

from src.lib.errors import *
from src.lib.send import receive_file_stop_wait, send_file_stop_wait

CHUNK_SIZE = 1024
TIMEOUT = 3


class _Uploader:
    def __init__(self, storage: str, addr, file_name: str):
        self.storage = storage
        self.addr = addr
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.file = file_name

    def method(self):
        self.server.sendto(b'its a me', self.addr)
        receive_file_stop_wait(self.server, f"{self.storage}/{self.file}", self.addr, set())
        print(f"file {self.file} written")


class _Downloader:
    def __init__(self, storage: str, addr, file_name: str):
        self.storage = storage
        self.addr = addr
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.file = file_name
        self.server.settimeout(TIMEOUT)

    def method(self):
        send_file_stop_wait(self.server, f"{self.storage}/{self.storage}", self.addr)
        print(f"file finished to send")


def get_data(data: bytes) -> List[str]:
    data = str(data, "utf-8").split()
    if len(data) != 2:
        raise InvalidAmountOfParametersError(f"amount of parameters is {len(data)}")
    return data


class Server:
    def __init__(self, host: str, port: int, storage: str = "./etc"):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind((host, port))
        self.path = storage
        self.connections = set()
        self.classes = {"upload": _Uploader, "download": _Downloader}

    def listen(self):
        print("server started to listen")
        while True:
            data, addr = self.server.recvfrom(CHUNK_SIZE)
            try:
                intention, file_name = get_data(data)
                class_to_use = self.classes.get(intention)
                if not class_to_use:
                    raise InvalidIntentionError
            except InvalidAmountOfParametersError:
                self.server.sendto(b'invalid parameters', addr)
                continue
            except InvalidIntentionError:
                self.server.sendto(b'invalid intention, should be upload or download', addr)
                continue
            print("client accepted")
            mini_server = class_to_use(self.path, addr, file_name)
            t = threading.Thread(target=mini_server.method, daemon=True)
            self.connections.add(t)
            t.start()
            print("mini server fired")


if __name__ == "__main__":
    s = Server("0.0.0.0", 80)
    s.listen()
