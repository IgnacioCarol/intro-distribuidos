import socket
import uuid
from typing import List
import src.lib.utils as lib_utils
import logging


def send_file(socket_connected, filename: str, address):
    eof_counter = 0
    with open(filename, "rb") as f:
        key = uuid.uuid4().bytes
        data_to_send = lib_utils.read_file(f, key)
        while data_to_send:
            msg = lib_utils.write_message(key, data_to_send)
            socket_connected.sendto(msg, address)
            try:
                data, address = socket_connected.recvfrom(lib_utils.BUFFER_SIZE)
            except socket.timeout:
                logging.info("timeout")
                if eof_counter > lib_utils.ENDING_LIMIT:
                    break
                if len(msg) < lib_utils.BUFFER_SIZE - len(key):
                    eof_counter += 1

                continue
            key = uuid.uuid4().bytes
            data_to_send = lib_utils.read_file(f, key)


def _get_message(message: bytes) -> List[bytes]:
    return [message[:16], message[16:]]


def receive_file(socket_connected, path: str, address, processed):
    with open(path, "wb") as f:
        while True:
            key, datachunk = _get_message(
                socket_connected.recvfrom(lib_utils.BUFFER_SIZE)[0]
            )
            socket_connected.sendto(key, address)
            if key in processed:
                continue
            processed.add(key)
            f.write(datachunk)
            if len(datachunk) < lib_utils.BUFFER_SIZE - len(key):
                break
    logging.info(f"finished receiving and storing file at {path}")


