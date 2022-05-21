import socket
from src.lib.send import send_file_stop_wait

TIMEOUT = 3
BUFFER_SIZE = 1024


class Upload:
    def __init__(self, host: str, port: int, file_name):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = host
        self.port = port
        self.client.settimeout(TIMEOUT)
        self.filename = file_name

    def send(self):
        print("client sending")
        addr = self.connect("upload")
        send_file_stop_wait(s.client, self.filename, addr)

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
    s = Upload("0.0.0.0", 80, "lorem_ipsum.txt")
    s.send()