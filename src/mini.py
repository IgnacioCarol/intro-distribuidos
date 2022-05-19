import socket


class Client:
    def __init__(self, host: str, port: int):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = host
        self.port = port

    def send(self):
        print("client sending")
        s.client.sendto(b'connect', (self.host, self.port))
        _, addr = s.client.recvfrom(1024)
        with open("lorem_ipsum.txt", "rb") as f:
            data_to_send = f.read()
        for i in range(0, len(data_to_send), 1024):
            data = self.client.sendto(data_to_send[i:i+1024], addr)
        print('esperando respuesta')
        _, addr = s.client.recvfrom(1024)
        print("Returned:")


if __name__ == "__main__":
    s = Client("0.0.0.0", 80)
    s.send()
