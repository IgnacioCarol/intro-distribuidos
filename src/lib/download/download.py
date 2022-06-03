import socket
import lib.errors as lib_errors
import lib.protocol as lib_protocol
import logging


class Download:
    def __init__(self, host: str, port: int, file_name, path: str):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = host
        self.port = port
        self.filename = file_name
        self.path = path

    def _receive(self, addr):
        pass

    def receive(self):
        try:
            logging.info("[Download] Client will try to connect...")
            addr = self.connect(lib_protocol.MSG_INTENTION_DOWNLOAD)
            logging.info("[Download] Client will start to recieve...")
            self._receive(addr)
        except lib_errors.ServerNotAvailable:
            logging.info("[Download] ERROR: Server not available...")
            return
        except OSError:
            logging.debug("[Download] Socket closed")
            return
        except (FileNotFoundError, IOError):
            logging.debug("[Download] ERROR: Client file not found.")
            return
        except Exception as e:
            logging.info("[Download] ERROR: Unexpected exception: {}.".format(e))
            return

    def connect(self, intention: str) -> tuple:
        """
        :param intention: to try to upload or download a file from the server
        :return tuple with value of host and port to connect
        """
        addr = ()
        while True:
            logging.debug("[Download] Trying to send download intention to server")
            self.client.sendto(
                bytes(f"{intention} {self.filename}", lib_protocol.ENCODING),
                (self.host, self.port),
            )
            try:
                logging.debug("[Download] Client tries to recieve ACK.")
                data, addr = self.client.recvfrom(lib_protocol.BUFFER_SIZE)
                parsed_data = str(data, lib_protocol.ENCODING)
                if parsed_data != lib_protocol.MSG_CONNECTION_ACK:
                    logging.debug("[Download]Error: " + parsed_data)
                    raise lib_errors.ServerNotAvailable()
                logging.debug("[Download] Client recieved ACK.")
                break
            except socket.timeout:
                logging.debug("[Download] Timeout waiting package from server")
                continue
        return addr

    def close(self):
        logging.info("[Download] Client is closing...")
        self.client.close()
