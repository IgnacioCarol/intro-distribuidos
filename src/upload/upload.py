import socket
import lib.errors as lib_errors
import lib.send as lib_send
import lib.protocol as lib_protocol
import logging


class Upload:
    def __init__(self, host: str, port: int, file_name):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = host
        self.port = port
        self.client.settimeout(lib_protocol.TIMEOUT_UPLOAD)
        self.filename = file_name

    def _send(self, addr):
        pass

    def send(self):
        logging.info("[Upload] Client starts send...")
        try:
            logging.info("[Upload] Client will try to connect...")
            addr = self.connect(lib_protocol.MSG_INTENTION_UPLOAD)
            logging.info("[Upload] Client will start to send...")
            self._send(addr)
        except lib_errors.ServerNotAvailable:
            logging.info("[Upload] ERROR: Server not available...")
            return
        except (FileNotFoundError, IOError) as e:
            logging.info("[Upload] ERROR: Client file not found.")
            raise e
        except Exception as e:
            logging.info("[Upload] ERROR: Unexpected exception: {}.".format(e))
            return

    def connect(self, intention: str) -> tuple:
        """
        :param intention: to try to upload or download a file from the server
        :return tuple with value of host and port to connect
        """

        addr = ()
        while True:
            logging.info("[Upload] Client sends its intention of uploading.")
            self.client.sendto(
                bytes(f"{intention} {self.filename}", lib_protocol.ENCODING),
                (self.host, self.port),
            )
            try:
                logging.info("[Upload] Client tries to recieve ACK.")
                data, addr = self.client.recvfrom(1024)
                parsed_data = str(data, lib_protocol.ENCODING)
                if parsed_data != lib_protocol.MSG_CONNECTION_ACK:
                    logging.info("[Upload] Client did not recieve ACK.")
                    raise lib_errors.ServerNotAvailable()
                logging.info("[Upload] Client recieved ACK.")
                break
            except socket.timeout:
                logging.info("[Upload] Client timeout.")
                continue
        return addr

    def close(self):
        logging.info("[Upload] Client is closing...")
        self.client.close()


class UploadStopAndWait(Upload):
    def _send(self, addr):
        lib_send.send_file_stop_and_wait(self.client, self.filename, addr)


class UploadSelectAndRepeat(Upload):
    def _send(self, addr):
        lib_send.send_file_select_and_repeat(self.client, self.filename, addr)
