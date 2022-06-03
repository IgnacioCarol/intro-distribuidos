import socket
import lib.errors as lib_errors
import lib.protocol as lib_protocol
import logging


class Upload:
    def __init__(self, host: str, port: int, file_name: str, path: str):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = host
        self.port = port
        self.client.settimeout(lib_protocol.TIMEOUT_UPLOAD)
        self.filename = file_name
        self.path = path

    def _send(self, addr):
        pass

    def send(self):
        logging.info("[Upload] Client starts send...")
        try:
            logging.info("[Upload] Client will try to connect...")
            addr = self.connect(lib_protocol.MSG_INTENTION_UPLOAD)
            logging.info("[Upload] Client will start to send...")
            self.filename = f"{self.path}/{self.filename}"
            self._send(addr)
        except lib_errors.ServerNotAvailable:
            logging.info("[Upload] ERROR: Server not available...")
            return
        except OSError:
            logging.debug("[Download] Socket closed")
            return
        except (FileNotFoundError, IOError) as e:
            logging.info("[Upload] ERROR: Client file not found.")
            raise e
        except Exception as e:
            logging.info("[Upload] ERROR: Unexpected exception: {}.".format(e))
            return
        finally:
            self.client.close()

    def connect(self, intention: str) -> tuple:
        """
        :param intention: to try to upload or download a file from the server
        :return tuple with value of host and port to connect
        """

        addr = ()
        while True:
            logging.debug("[Upload] Trying to send download intention to server.")
            self.client.sendto(
                bytes(f"{intention} {self.filename}", lib_protocol.ENCODING),
                (self.host, self.port),
            )
            try:
                logging.debug("[Upload] Client tries to recieve ACK.")
                data, addr = self.client.recvfrom(1024)
                parsed_data = str(data, lib_protocol.ENCODING)
                if parsed_data != lib_protocol.MSG_CONNECTION_ACK:
                    logging.debug("[Upload] Client did not recieve ACK.")
                    raise lib_errors.ServerNotAvailable()
                logging.debug("[Upload] Client recieved ACK.")
                break
            except socket.timeout:
                logging.debug("[Upload] Client timeout.")
                continue
        return addr

    def close(self):
        logging.info("[Upload] Client is closing...")
        self.client.close()
