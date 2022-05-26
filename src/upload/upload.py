import socket
import lib.errors as lib_errors
import lib.send as lib_send
import lib.protocol as lib_protocol


class Upload:
    def __init__(self, host: str, port: int, file_name):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = host
        self.port = port
        self.client.settimeout(lib_protocol.TIMEOUT_UPLOAD)
        self.filename = file_name

    def send(self):
        print("client sending")
        try:
            addr = self.connect(lib_protocol.MSG_INTENTION_UPLOAD)
            lib_send.send_file_select_and_repeat(self.client, self.filename, addr)
        except lib_errors.ServerNotAvailable:
            return
        except (FileNotFoundError, IOError) as e:
            raise e
        except Exception:
            print("Error: Se recibió una excepción no manejada")
            return

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
                data, addr = self.client.recvfrom(1024)
                parsed_data = str(data, lib_protocol.ENCODING)
                if parsed_data != lib_protocol.MSG_CONNECTION_ACK:
                    print("Error: " + parsed_data)
                    raise lib_errors.ServerNotAvailable()
                break
            except socket.timeout:
                continue
        return addr

    def close(self):
        print("El cliente se esta cerrando")
        self.client.close()
