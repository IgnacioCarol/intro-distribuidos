from os import path
import socket
import lib.archive as arc
import lib.protocol as lib_protocol
import logging

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
            self.archive.release_ownership(self.addr, self.file)
            logging.info("[server-downloader] Release ownership {}.".format(self.file))
        except arc.FileNotInArchiveError:
            logging.info("[server-downloader] ERROR: File {self.file} not in archive.")
        except arc.FileNotOwnedError:
            logging.info("[server-downloader] ERROR: File {self.file} not owned.")

    def method(self):

        # Set ownership of file
        if not path.exists(f"{self.storage}/{self.file}"):
            self._handle_release()
            self.server.sendto(
                bytes(lib_protocol.ERROR_NONEXISTENT_FILE, lib_protocol.ENCODING),
                self.addr,
            )
            return
        try:
            logging.info(
                "[start-server][downloader] Set ownership {}->{}.".format(
                    self.file, self.addr
                )
            )
            if not self.archive.set_ownership(self.addr, self.file, False):
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
        self.server.sendto(
            bytes(lib_protocol.MSG_CONNECTION_ACK, lib_protocol.ENCODING), self.addr
        )
        self._send()
        logging.info(f"File {self.file} sent")
        self._handle_release()