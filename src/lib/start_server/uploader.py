import socket
import lib.archive as arc
import lib.protocol as lib_protocol
import logging


class _Uploader:
    def __init__(self, storage: str, addr, file_name: str, archive):
        self.storage = storage
        self.addr = addr
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.file = file_name
        self.server.settimeout(lib_protocol.TIMEOUT_UPLOAD)
        self.archive = archive

    def _receive(self):
        raise Exception("not defined")

    def _handle_release(self):
        try:
            self.archive.release_ownership(self.addr, self.file)
            logging.info(f"[start-server][uploader] Release ownership  {self.file}.")
        except arc.FileNotInArchiveError:
            logging.info(
                f"[start-server][uploader] ERROR: File {self.file} not in archive."
            )
        except arc.FileNotOwnedError:
            logging.info(f"[start-server][uploader] ERROR: File {self.file} not owned.")

    def method(self):

        # Set ownership of file
        try:
            logging.info(
                "[start-server][uploader] Set ownership {}->{}.".format(
                    self.file, self.addr
                )
            )
            if not self.archive.set_ownership(self.addr, self.file, True):
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
            self._handle_release()
            return
