import socket
from time import sleep
import uuid

from typing import List

BUFFER_SIZE = 1024
SEPARATOR = b""
ENDING_LIMIT = 10  # times to wait for the ack when finishing sending the file


def write_message(key: bytes, message: bytes) -> bytes:
    return key + SEPARATOR + message


def send_file_stop_wait(socket_connected, filename: str, address):
    eof_counter = 0
    with open(filename, "rb") as f:
        key = uuid.uuid4().bytes
        data_to_send = read_file(f, key)
        while data_to_send:
            sleep(5)
            msg = write_message(key, data_to_send)
            socket_connected.sendto(msg, address)
            try:
                data, address = socket_connected.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                if eof_counter > ENDING_LIMIT:
                    break
                if len(msg) < BUFFER_SIZE - len(key) - len(SEPARATOR):
                    eof_counter += 1
                print("timeouteo")
                continue
            key = uuid.uuid4().bytes
            data_to_send = read_file(f, key)


def read_file(f, key):
    return f.read(BUFFER_SIZE - len(key) - len(SEPARATOR))


def _get_message(message: bytes) -> List[bytes]:
    return [message[:16], message[16:]]


def receive_file_stop_wait(socket_connected, path: str, address, processed):
    with open(path, "wb") as f:
        while True:
            key, datachunk = _get_message(socket_connected.recvfrom(BUFFER_SIZE)[0])
            socket_connected.sendto(key, address)
            if key in processed:
                continue
            processed.add(key)
            f.write(datachunk)
            if len(datachunk) < BUFFER_SIZE - len(key) - len(SEPARATOR):
                break
    print(f"finished receiving and storing file at {path}")
