import os
import socket
import lib.errors as lib_errors
import lib.selective_repeat as selective_repeat
import lib.stop_wait as stop_and_wait
import lib.protocol as lib_protocol
import logging


class Download:
    def __init__(self, host: str, port: int, file_name, path: str):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = host
        self.port = port
        self.filename = file_name
        self.path = path

    def _receive(self, addr):
        pass

    def receive(self):
        try:
            logging.info("[Download] Client will try to connect...")
            addr = self.connect(lib_protocol.MSG_INTENTION_DOWNLOAD)
            logging.info("[Download] Client will start to recieve...")
            self._receive(addr)
        except lib_errors.ServerNotAvailable:
            logging.info("[Download] ERROR: Server not available...")
            return
        except (FileNotFoundError, IOError) as e:
            logging.info("[Download] ERROR: Client file not found.")
            raise e
        except Exception as e:
            logging.info("[Download] ERROR: Unexpected exception: {}.".format(e))
            return

    def connect(self, intention: str) -> tuple:
        """
        :param intention: to try to upload or download a file from the server
        :return tuple with value of host and port to connect
        """
        addr = ()
        while True:
            self.client.sendto(
                bytes(f"{intention} {self.filename}", lib_protocol.ENCODING),
                (self.host, self.port),
            )
            try:
                data, addr = self.client.recvfrom(lib_protocol.BUFFER_SIZE)
                parsed_data = str(data, lib_protocol.ENCODING)
                if parsed_data != lib_protocol.MSG_CONNECTION_ACK:
                    logging.info("Error: " + parsed_data)
                    raise lib_errors.ServerNotAvailable()
                break
            except socket.timeout:
                continue
        return addr


class DownloadStopAndWait(Download):
    def _receive(self, addr):
        file_path = "{}/{}".format(self.path, self.filename)
        return stop_and_wait.receive_file(self.client, file_path, addr, set())


class DownloadSelectiveRepeat(Download):
    def _receive(self, addr):
        file_path = "{}/{}".format(os.getcwd(), self.filename)
        return selective_repeat.receive_file(self.client, file_path, addr)
