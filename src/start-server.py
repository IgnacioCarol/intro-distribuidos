import socket
import time
import threading

CHUNK_SIZE = 1024
TIMEOUT = 3


class _Server:
    def __init__(self, storage: str, addr, file_name: str):
        self.storage = storage
        self.addr = addr
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.file = file_name
        self.server.settimeout(TIMEOUT)

    def receive(self):
        data = []
        self.server.sendto(b'its a me', self.addr)
        while True:
            datachunk = self.server.recvfrom(CHUNK_SIZE)
            data.append(datachunk[0])
            
            self.server.sendto(b'ok', self.addr)
            if len(datachunk[0]) < CHUNK_SIZE:
                print(len(datachunk[0]))
                break
        with open(f"{self.storage}/{self.file}", "wb") as f:
            f.writelines(data)
        self.server.sendto(b'finished', self.addr)
        while True:
            pass


def get_file_name(data: bytes) -> str:
    return str(data, "utf-8").split()[-1]


class Server:
    def __init__(self, host: str, port: int, storage: str = "./etc"):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind((host, port))
        self.path = storage
        self.connections = set()

    def listen(self):
        print("server started to listen")
        while True:
            data, addr = self.server.recvfrom(CHUNK_SIZE)
            file_name = get_file_name(data)
            print("server aceptado")
            mini_server = _Server(self.path, addr, file_name)
            t = threading.Thread(target=mini_server.receive, daemon=True)
            self.connections.add(t)
            t.start()
            print("server disparado")


if __name__ == "__main__":
    s = Server("0.0.0.0", 80)
    s.listen()
