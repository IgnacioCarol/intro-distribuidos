import socket
import threading
import lib.archive as arc
import lib.errors as lib_errors
from lib.send import receive_file_select_and_repeat, send_file_select_and_repeat
from lib.protocol import *
from typing import List
from os import path

class _Uploader:
    def __init__(self, storage: str, addr, file_name: str, archive):
        self.storage = storage
        self.addr = addr
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.file = file_name
        self.server.settimeout(TIMEOUT_UPLOAD)
        self.archive = archive

    def _handle_release(self):
        try:
            self.archive.releaseOwnership(self.addr, self.file)
        except arc.FileNotInArchiveError:
            print("Error: FileNotInArchiveError")
        except arc.FileNotOwnedError:
            print("Error: FileNotOwnedError")

    def method(self):
        try:
            if not self.archive.setOwnership(self.addr, self.file, True):
                self.server.sendto(bytes(ERROR_BUSY_FILE, ENCODING), self.addr)
                return
        except arc.FileAlreadyOwnedError:
            self.server.sendto(bytes(ERROR_ALREADY_SERVED, ENCODING), self.addr)
            return

        self.server.sendto(bytes(MSG_CONNECTION_ACK,ENCODING), self.addr)
        try:
            receive_file_select_and_repeat(
                self.server, f"{self.storage}/{self.file}", self.addr, set()
            )
        except socket.timeout:
            print("se manejo timeout en upload del server")
            self._handle_release()
            return

        print(f"file {self.file} written")
        self._handle_release()


# Fixme there is a border case where it could be repeated for the same address multiple senders
class _Downloader:
    def __init__(self, storage: str, addr, file_name: str, archive):
        self.storage = storage
        self.addr = addr
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.file = file_name
        self.server.settimeout(TIMEOUT_DOWNLOAD)
        self.archive = archive

    def _handle_release(self):
        try:
            self.archive.releaseOwnership(self.addr, self.file)
        except arc.FileNotInArchiveError:
            print("Error: FileNotInArchiveError")
        except arc.FileNotOwnedError:
            print("Error: FileNotOwnedError")

    def method(self):
        try:
            if not self.archive.setOwnership(self.addr, self.file, False):
                self.server.sendto(bytes(ERROR_BUSY_FILE, ENCODING), self.addr)
                return
        except arc.FileAlreadyOwnedError:
            self.server.sendto(bytes(ERROR_ALREADY_SERVED, ENCODING), self.addr)
            return

        if not path.exists(self.file):
            self._handle_release()
            self.server.sendto(bytes(ERROR_NONEXISTENT_FILE, ENCODING), self.addr)
            return
        self.server.sendto(bytes(MSG_CONNECTION_ACK,ENCODING), self.addr)
        send_file_select_and_repeat(self.server, f"{self.storage}/{self.file}", self.addr)
        print("file finished to send")
        self._handle_release()


def get_data(data: bytes) -> List[str]:
    data = str(data, ENCODING).split()
    if len(data) != 2:
        raise lib_errors.InvalidAmountOfParametersError(
            f"amount of parameters is {len(data)}"
        )
    return data


class Server:
    def __init__(self, host: str, port: int, storage: str = "./etc"):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind((host, port))
        self.path = storage
        self.connections = set()
        self.classes = {MSG_INTENTION_UPLOAD: _Uploader, MSG_INTENTION_DOWNLOAD: _Downloader}
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
                    raise lib_errors.InvalidIntentionError
            except lib_errors.InvalidAmountOfParametersError:
                self.server.sendto(bytes(ERROR_INVALID_PARAMETERS, ENCODING), addr)
                continue
            except lib_errors.InvalidIntentionError:
                self.server.sendto(
                    bytes(ERROR_INVALID_INTENTION, ENCODING), addr
                )
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
