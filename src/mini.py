import socket
import time

TIMEOUT = 3
BUFFER_SIZE = 1024


class Client:
    def __init__(self, host: str, port: int, file_name):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = host
        self.port = port
        self.client.settimeout(TIMEOUT)
        self.filename = file_name

    # Implemented with stop&wait
    # FixMe make it general for selective repeat
    def send(self):
        print("client sending")
        s.client.sendto(bytes(f"upload {self.filename}", "utf-8"), (self.host, self.port))
        _, addr = s.client.recvfrom(1024)
        with open(self.filename, "rb") as f:
            data_to_send = f.read()
        i = 0
        while i < len(data_to_send):
            self.client.sendto(data_to_send[i:i + 1024], addr)
            data, addr = self.client.recvfrom(BUFFER_SIZE)
            if data:
                i += BUFFER_SIZE
        print('esperando respuesta')
        _, addr = s.client.recvfrom(1024)
        print("Archivo enviado")


if __name__ == "__main__":
    s = Client("0.0.0.0", 80, "lorem_ipsum.txt")
    s.send()
