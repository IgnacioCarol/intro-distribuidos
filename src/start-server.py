import socket
import threading
import archive as arc
from typing import List
from lib.handler import InterruptHandler
from lib.errors import *
from lib.send import receive_file_stop_wait, send_file_stop_wait

CHUNK_SIZE = 1024
TIMEOUT = 3
TIMEOUT_UPLOAD = 15

class _Uploader:
    def __init__(self, storage: str, addr, file_name: str, archive):
        self.storage = storage
        self.addr = addr
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.file = file_name
        self.server.settimeout(TIMEOUT_UPLOAD)
        self.archive = archive

    def method(self):
        try:
            if not self.archive.setOwnership(self.addr, self.file, True):
                self.server.sendto(b'try later', self.addr)
                return
        except arc.FileAlreadyOwnedError:
            self.server.sendto(b'already served', self.addr)
            return

        self.server.sendto(b'its a me', self.addr)
        try:
            receive_file_stop_wait(self.server, f"{self.storage}/{self.file}", self.addr, set())
        except socket.timeout:
            print("se manejo timeout en upload del server")
            try:
                self.archive.releaseOwnership(self.addr, self.file)
            except arc.FileNotInArchiveError:
                print('Error: FileNotInArchiveError')
            except arc.FileNotOwnedError:
                print('Error: FileNotOwnedError')
            return
        print(f"file {self.file} written")

        try:
            self.archive.releaseOwnership(self.addr, self.file)
        except arc.FileNotInArchiveError:
            print('Error: FileNotInArchiveError')
        except arc.FileNotOwnedError:
            print('Error: FileNotOwnedError')

# Fixme there is a border case where it could be repeated for the same address multiple senders
class _Downloader:
    def __init__(self, storage: str, addr, file_name: str, archive):
        self.storage = storage
        self.addr = addr
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.file = file_name
        self.server.settimeout(TIMEOUT)
        self.archive = archive

    def method(self):
        try:
            if not self.archive.setOwnership(self.addr, self.file, False):
                self.server.sendto(b'try later', self.addr)
                return
        except archive.FileAlreadyOwnedError:
            self.server.sendto(b'already served', self.addr)
            return
        send_file_stop_wait(self.server, f"{self.storage}/{self.file}", self.addr)
        print(f"file finished to send")

        try:
            self.archive.releaseOwnership(self.addr, self.file)
        except arc.FileNotInArchiveError:
            print('Error: FileNotInArchiveError')
        except arc.FileNotOwnedError:
            print('Error: FileNotOwnedError')

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
        self.stoped = False
        self.archive = arc.Archive()

    def listen(self):
        print("server started to listen")
        while not self.stoped:
            try:
                data, addr = self.server.recvfrom(CHUNK_SIZE)
            except OSError:
                print("socket cerrado")
                continue
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
            mini_server = class_to_use(self.path, addr, file_name, self.archive)
            t = threading.Thread(target=mini_server.method)
            self.connections.add(t)
            t.start()
            print("mini server fired")

    def close(self):
        self.stoped = True
        self.server.close()
        print("Server closed")
        self.__joinConnections()
        

    def __joinConnections(self):
        for connection in self.connections:
            connection.join()

if __name__ == "__main__":
    with InterruptHandler() as handler:
        s = Server("127.0.0.1", 80)
        handler.listener(s.close)
        s.listen()
