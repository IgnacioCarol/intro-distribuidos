import socket
from src.lib.send import receive_file_stop_wait

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
        addr = self.connect("download")
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
                _, addr = s.client.recvfrom(1024)
                break
            except socket.timeout:
                continue
        return addr


if __name__ == "__main__":
    s = Download("0.0.0.0", 80, "lorem_ipsum.txt", "./etc/downloaded")
    s.receive()
