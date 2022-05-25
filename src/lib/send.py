import socket
import uuid
from io import TextIOWrapper
from msilib.schema import File
from time import sleep
from typing import List
from lib.timer import RepeatingTimer
from protocol import *

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


def _send_callback(socket_connected, address, data_to_send, key):
    msg = write_message(bytes(key, ENCODING), data_to_send)
    socket_connected.sendto(msg, address)

def _send_data(timers: List[RepeatingTimer], socket_connected: socket.socket, address: str, data_to_send: str, last_chunk_sent: int):
    _send_callback(socket_connected, address, data_to_send, last_chunk_sent)
    timers.append(RepeatingTimer(10.0, _send_callback, [socket_connected, address, data_to_send, last_chunk_sent]))
    timers[-1].start()

def send_file_select_and_repeat(socket_connected: socket.socket, filename: str, address: str):
#   socket_connected.setblocking(False)
    with open(filename, "rb") as f:
        timers = []
        last_chunk_sent = 0
        latest_ack = 0
        data_to_send = read_file(f, last_chunk_sent)

        while data_to_send and last_chunk_sent < WINDOW_SIZE:
            _send_data(timers, socket_connected, address, data_to_send, last_chunk_sent)
            data_to_send = read_file(f, last_chunk_sent)
            last_chunk_sent += 1

        while data_to_send:
            try:
                ack, address = socket_connected.recvfrom(BUFFER_SIZE)
                for i in range(latest_ack, ack):
                    timers[i].cancel()
                    timers.pop(i)

                latest_ack = ack - 1
            except socket.timeout:
                print("timeouteo")
                continue

            for i in range(WINDOW_SIZE - len(timers)):
                _send_data(timers, socket_connected, address, data_to_send, last_chunk_sent)
                data_to_send = read_file(f, last_chunk_sent)
                last_chunk_sent += 1

def read_file(f: TextIOWrapper, key):
    return f.read(BUFFER_SIZE - len(key) - len(SEPARATOR))

def _get_message_stop_wait(message: bytes) -> List[bytes]:
    return [message[:16], message[16:]]

def receive_file_stop_wait(socket_connected, path: str, address, processed):
    with open(path, "wb") as f:
        while True:
            key, datachunk = _get_message_stop_wait(socket_connected.recvfrom(BUFFER_SIZE)[0])
            socket_connected.sendto(key, address)
            if key in processed:
                continue
            processed.add(key)
            f.write(datachunk)
            if len(datachunk) < BUFFER_SIZE - len(key) - len(SEPARATOR):
                break
    print(f"finished receiving and storing file at {path}")
