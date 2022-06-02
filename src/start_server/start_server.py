import socket
import threading
import src.lib.archive as arc
import src.lib.errors as lib_errors
import src.lib.stop_wait as stop_and_wait
import src.lib.selective_repeat as selective_repeat
import src.lib.protocol as lib_protocol
from typing import List
from os import path
import logging
from src.lib.logger import Logger


class _Uploader:
    def __init__(self, storage: str, addr, file_name: str, archive):
        self.storage = storage
        self.addr = addr
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.file = file_name
        self.server.settimeout(lib_protocol.TIMEOUT_UPLOAD)
        self.archive = archive

    def _receive(self):
        pass

    def _handle_release(self):
        try:
            self.archive.releaseOwnership(self.addr, self.file)
            logging.info("[start-server][uploader] Release ownership  {self.file}.")
        except arc.FileNotInArchiveError:
            logging.info(
                "[start-server][uploader] ERROR: File {self.file} not in archive."
            )
        except arc.FileNotOwnedError:
            logging.info("[start-server][uploader] ERROR: File {self.file} not owned.")

    def method(self):

        # Set ownership of file
        try:
            logging.info(
                "[start-server][uploader] Set ownership {}->{}.".format(
                    self.file, self.addr
                )
            )
            if not self.archive.setOwnership(self.addr, self.file, True):
                self.server.sendto(
                    bytes(lib_protocol.ERROR_BUSY_FILE, lib_protocol.ENCODING),
                    self.addr,
                )
                logging.info(
                    "[start-server][uploader] ERROR Ownership busy of file: {}.".format(
                        self.file
                    )
                )
                return
        except arc.FileAlreadyOwnedError:
            self.server.sendto(
                bytes(lib_protocol.ERROR_ALREADY_SERVED, lib_protocol.ENCODING),
                self.addr,
            )
            logging.info(
                "[start-server][uploader] ERROR: File {} has already been served.".format(
                    self.file
                )
            )
            return

        # Sends SYNC-ACK
        logging.info(
            "[start-server][uploader] Sends SYC-ACK to client {}.".format(self.addr)
        )
        self.server.sendto(
            bytes(lib_protocol.MSG_CONNECTION_ACK, lib_protocol.ENCODING), self.addr
        )

        try:
            self._receive()
        except socket.timeout:
            print("se manejo timeout en upload del server")
            self._handle_release()
            return

        logging.info(f"file {self.file} written")
        self._handle_release()


# Fixme there is a border case where it could be repeated for the same address multiple senders
class _Downloader:
    def __init__(self, storage: str, addr, file_name: str, archive):
        self.storage = storage
        self.addr = addr
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.file = file_name
        self.server.settimeout(lib_protocol.TIMEOUT_DOWNLOAD)
        self.archive = archive

    def _send(self):
        pass

    def _handle_release(self):
        try:
            self.archive.releaseOwnership(self.addr, self.file)
            logging.info("[server-downloader] Release ownership {}.".format(self.file))
        except arc.FileNotInArchiveError:
            logging.info("[server-downloader] ERROR: File {self.file} not in archive.")
        except arc.FileNotOwnedError:
            logging.info("[server-downloader] ERROR: File {self.file} not owned.")

    def method(self):

        # Set ownership of file
        try:
            logging.info(
                "[start-server][downloader] Set ownership {}->{}.".format(
                    self.file, self.addr
                )
            )
            if not self.archive.setOwnership(self.addr, self.file, True):
                self.server.sendto(
                    bytes(lib_protocol.ERROR_BUSY_FILE, lib_protocol.ENCODING),
                    self.addr,
                )
                logging.info(
                    "[start-server][downloader] ERROR Ownership busy of file: {}.".format(
                        self.file
                    )
                )
                return
        except arc.FileAlreadyOwnedError:
            self.server.sendto(
                bytes(lib_protocol.ERROR_ALREADY_SERVED, lib_protocol.ENCODING),
                self.addr,
            )
            logging.info(
                "[start-server][downloader] ERROR: File {} has already been served.".format(
                    self.file
                )
            )
            return

        if not path.exists(f"{self.storage}/{self.file}"):
            self._handle_release()
            self.server.sendto(
                bytes(lib_protocol.ERROR_NONEXISTENT_FILE, lib_protocol.ENCODING),
                self.addr,
            )
            return
        self.server.sendto(
            bytes(lib_protocol.MSG_CONNECTION_ACK, lib_protocol.ENCODING), self.addr
        )
        self._send()
        logging.info(f"File {self.file} sent")
        self._handle_release()


def get_data(data: bytes) -> List[str]:
    data = str(data, lib_protocol.ENCODING).split()
    if len(data) != 2:
        raise lib_errors.InvalidAmountOfParametersError(
            f"amount of parameters is {len(data)}"
        )
    return data


class Server:
    def __init__(self, host: str, port: int, storage: str = "./etc", architecture=dict):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind((host, port))
        self.path = storage
        self.connections = set()
        self.classes = architecture
        self.stopped = False
        self.archive = arc.Archive()

    def listen(self):
        logging.info("[server] Server is listening...")
        while not self.stopped:
            try:
                data, addr = self.server.recvfrom(lib_protocol.CHUNK_SIZE)
                logging.info("[server] Server recieves data from {}...".format(addr))
            except OSError:
                logging.info("[server] Socket closed")
                continue
            try:
                intention, file_name = get_data(data)
                class_to_use = self.classes.get(intention)
                logging.info(
                    "[server] Server's client has an intention of {}ing file {}...".format(
                        intention, file_name
                    )
                )
                if not class_to_use:
                    logging.info(
                        "[server] Server does not recognize intention: {}".format(
                            intention
                        )
                    )
                    raise lib_errors.InvalidIntentionError
            except lib_errors.InvalidAmountOfParametersError:
                logging.info(
                    "[server] ERROR: Server gets an invalid amount of parameters."
                )
                self.server.sendto(
                    bytes(lib_protocol.ERROR_INVALID_PARAMETERS, lib_protocol.ENCODING),
                    addr,
                )
                continue
            except lib_errors.InvalidIntentionError:
                logging.info("[server] ERROR: Server gets an invalid intention.")
                self.server.sendto(
                    bytes(lib_protocol.ERROR_INVALID_INTENTION, lib_protocol.ENCODING),
                    addr,
                )
                continue

            logging.info("[server] Server accepts client {}.".format(addr))

            mini_server = class_to_use(self.path, addr, file_name, self.archive)
            t = threading.Thread(target=mini_server.method)
            self.connections.add(t)
            t.start()

            logging.info("[server] Server runs uploader.")

    def close(self):
        self.stopped = True
        self.server.close()
        logging.info("[server] Server closed.")
        self.__joinConnections()

    def __joinConnections(self):
        for connection in self.connections:
            connection.join()


class _UploaderStopAndWait(_Uploader):
    def _receive(self):
        return stop_and_wait.receive_file(
            self.server, f"{self.storage}/{self.file}", self.addr, set()
        )


class _UploaderSelectiveRepeat(_Uploader):
    def _receive(self):
        return selective_repeat.receive_file(
            self.server, f"{self.storage}/{self.file}", self.addr, set()
        )


class _DownloaderStopAndWait(_Downloader):
    def _send(self):
        return stop_and_wait.send_file(
            self.server, f"{self.storage}/{self.file}", self.addr
        )


class _DownloaderSelectiveRepeat(_Downloader):
    def _send(self):
        return selective_repeat.send_file(
            self.server, f"{self.storage}/{self.file}", self.addr
        )


class ServerStopAndWait(Server):
    def __init__(self, host: str, port: int, storage: str = "./etc"):

        architecture = {
            lib_protocol.MSG_INTENTION_UPLOAD: _UploaderStopAndWait,
            lib_protocol.MSG_INTENTION_DOWNLOAD: _DownloaderStopAndWait,
        }
        super().__init__(host, port, storage, architecture)


class ServerSelectiveRepeat(Server):
    def __init__(self, host: str, port: int, storage: str = "./etc"):

        architecture = {
            lib_protocol.MSG_INTENTION_UPLOAD: _UploaderSelectiveRepeat,
            lib_protocol.MSG_INTENTION_DOWNLOAD: _DownloaderSelectiveRepeat,
        }
        super().__init__(host, port, storage, architecture)


if __name__ == '__main__':
    Logger(True, False)
    server = ServerSelectiveRepeat('localhost', 8080)
    server.listen()
