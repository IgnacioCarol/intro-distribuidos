import socket
import uuid

from typing import List

BUFFER_SIZE = 1024
SEPARATOR = b'-'


def write_message(key: bytes, message: bytes) -> bytes:
    return key + SEPARATOR + message


def send_file_stop_wait(socket_connected, filename: str, address):
    with open(filename, "rb") as f:
        key = uuid.uuid4().bytes
        data_to_send = f.read(BUFFER_SIZE - len(key) - 1)
        while data_to_send:
            socket_connected.sendto(write_message(key, data_to_send), address)
            try:
                data, address = socket_connected.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                print("timeouteo")
                continue
            if data:
                key = uuid.uuid4().bytes
                data_to_send = f.read(BUFFER_SIZE - len(key) - 1)


def _get_message(message: bytes) -> List[bytes]:
    data = message.split(SEPARATOR)
    return [data[0], SEPARATOR.join(data[1:])]


def receive_file_stop_wait(socket_connected, path: str, address, processed):
    data = []
    while True:
        key, datachunk = _get_message(socket_connected.recvfrom(BUFFER_SIZE)[0])
        socket_connected.sendto(key, address)
        if key in processed:
            continue
        processed.add(key)
        data.append(datachunk)
        if len(datachunk) < BUFFER_SIZE - len(key) - len(SEPARATOR):
            break
    with open(path, "wb") as f:
        f.writelines(data)
    print(f"finished receiving and storing file at {path}")
    return data
