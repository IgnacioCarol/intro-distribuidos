import socket
import lib.errors as lib_errors
from lib.send import receive_file_stop_wait, receive_file_select_and_repeat
import lib.protocol as lib_protocol


class Download:
    def __init__(self, host: str, port: int, file_name, path: str):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = host
        self.port = port
        self.filename = file_name
        self.path = path

    def _receive(self, file, addr, processed):
        pass

    def receive(self):
        print("client receiving")
        try:
            addr = self.connect(lib_protocol.MSG_INTENTION_DOWNLOAD)
        except lib_errors.ServerNotAvailable:
            return self._receive(addr)

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
                    print("Error: " + parsed_data)
                    raise lib_errors.ServerNotAvailable()
                break
            except socket.timeout:
                continue
        return addr


class DownloadStopAndWait(Download):
    def _receive(self, addr):
        return receive_file_stop_wait(
            self.client, f"{self.path}/{self.filename}", addr, set()
        )


class DownloadSelectAndRepeat(Download):
    def _receive(self, addr):
        return receive_file_select_and_repeat(
            self.client, f"{self.path}/{self.filename}", addr, set()
        )
