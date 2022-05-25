import socket
import lib.errors as lib_errors
from lib.send import receive_file_stop_wait
from lib.protocol import *

class Download:
    def __init__(self, host: str, port: int, file_name, path: str):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = host
        self.port = port
        self.filename = file_name
        self.path = path

    def receive(self):
        print("client receiving")
        try:
            addr = self.connect(MSG_INTENTION_DOWNLOAD)
        except lib_errors.ServerNotAvailable:
            return
        receive_file_stop_wait(self.client, f"{self.path}/{self.filename}", addr, set())

    def connect(self, intention: str) -> tuple:
        """
        :param intention: to try to upload or download a file from the server
        :return tuple with value of host and port to connect
        """
        addr = ()
        while True:
            self.client.sendto(
                bytes(f"{intention} {self.filename}", ENCODING), (self.host, self.port)
            )
            try:
                data, addr = self.client.recvfrom(BUFFER_SIZE)
                parsed_data = str(data, ENCODING)
                if parsed_data != MSG_CONNECTION_ACK:
                    print("Error: " + parsed_data)
                    raise lib_errors.ServerNotAvailable()
                break
            except socket.timeout:
                continue
        return addr
