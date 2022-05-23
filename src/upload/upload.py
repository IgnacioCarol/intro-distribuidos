import socket
import lib.errors as lib_errors
from lib.send import send_file_stop_wait

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
        try:
            addr = self.connect("upload")
            send_file_stop_wait(self.client, self.filename, addr)
        except lib_errors.ServerNotAvailable:
            return
        except Exception:
            return

    def connect(self, intention: str) -> tuple:
        """
        :param intention: to try to upload or download a file from the server
        :return tuple with value of host and port to connect
        """
        addr = ()
        while True:
            self.client.sendto(
                bytes(f"{intention} {self.filename}", "utf-8"), (self.host, self.port)
            )
            try:
                data, addr = self.client.recvfrom(1024)
                parsed_data = str(data, "utf-8")
                if parsed_data != "its a me":
                    print("Error: " + parsed_data)
                    raise lib_errors.ServerNotAvailable()
                break
            except socket.timeout:
                continue
        return addr

    def close(self):
        print("El cliente se esta cerrando")
        self.client.close()
