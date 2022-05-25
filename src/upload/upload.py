import socket
import lib.errors as lib_errors
from lib.send import *
from lib.protocol import *

class Upload:
    def __init__(self, host: str, port: int, file_name):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = host
        self.port = port
        self.client.settimeout(TIMEOUT_UPLOAD)
        self.filename = file_name

    def send(self):
        print("client sending")
        try:
            addr = self.connect(MSG_INTENTION_UPLOAD)
            send_file_select_and_repeat(self.client, self.filename, addr)
        except lib_errors.ServerNotAvailable:
            return
        except (FileNotFoundError, IOError) as e:
            raise e
            print('Error: El archivo solicitado no existe')
            return
        except Exception as e:
            print('Error: Se recibió una excepción no manejada')
            return

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
                data, addr = self.client.recvfrom(1024)
                parsed_data = str(data, ENCODING)
                if parsed_data != MSG_CONNECTION_ACK:
                    print("Error: " + parsed_data)
                    raise lib_errors.ServerNotAvailable()
                break
            except socket.timeout:
                continue
        return addr

    def close(self):
        print("El cliente se esta cerrando")
        self.client.close()
