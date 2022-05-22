import socket

from lib.errors import *
from lib.send import receive_file_stop_wait

BUFFER_SIZE = 1024


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
            addr = self.connect("download")
        except ServerNotAvailable as e:
            return
        receive_file_stop_wait(s.client, f"{self.path}/{self.filename}", addr, set())

    def connect(self, intention: str) -> tuple:
        """
        :param intention: to try to upload or download a file from the server
        :return tuple with value of host and port to connect
        """
        addr = ()
        while True:
            s.client.sendto(bytes(f"{intention} {self.filename}", "utf-8"), (self.host, self.port))
            try:
                data, addr = s.client.recvfrom(1024)
                parsed_data =str(data, "utf-8")
                if(parsed_data !=  'its a me'):
                    print('Error: ' + parsed_data)
                    raise ServerNotAvailable()
                break
            except socket.timeout:
                continue
        return addr


if __name__ == "__main__":
    s = Download("localhost", 80, "lorem_ipsum.txt", "./etc/downloaded")
    s.receive()
