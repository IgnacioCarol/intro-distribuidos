import socket
import uuid
import heapq
import os
from io import TextIOWrapper
from typing import List
from lib.timer import RepeatingTimer
import lib.protocol as lib_protocol
import logging

BUFFER_SIZE = 1024
ENDING_LIMIT = 10  # times to wait for the ack when finishing sending the file


def write_message(key: bytes, message: bytes) -> bytes:
    return key + message


def send_file_stop_and_wait(socket_connected, filename: str, address):
    eof_counter = 0
    with open(filename, "rb") as f:
        key = uuid.uuid4().bytes
        data_to_send = read_file(f, key)
        while data_to_send:
            # sleep(5)
            msg = write_message(key, data_to_send)
            socket_connected.sendto(msg, address)
            try:
                data, address = socket_connected.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                logging.info("timeout")
                if eof_counter > ENDING_LIMIT:
                    break
                if len(msg) < BUFFER_SIZE - len(key):
                    eof_counter += 1

                continue
            key = uuid.uuid4().bytes
            data_to_send = read_file(f, key)


def _send_callback(socket_connected, address, data_to_send, key):
    data = bytes(
        f"{key:{lib_protocol.PADDING}>{lib_protocol.SEQ_LEN}}", lib_protocol.ENCODING
    )
    msg = write_message(data, data_to_send)
    socket_connected.sendto(msg, address)


def _send_data(
        timers: List[RepeatingTimer],
        socket_connected: socket.socket,
        address: str,
        data_to_send: str,
        key: str,
):
    _send_callback(socket_connected, address, data_to_send, key)
    timers.append(
        RepeatingTimer(
            lib_protocol.TIMEOUT_TIMER,
            _send_callback,
            socket_connected,
            address,
            data_to_send,
            key,
        )
    )
    timers[-1].start()


def read_file(f: TextIOWrapper, key):
    return f.read(BUFFER_SIZE - len(key))


def _get_message_stop_wait(message: bytes) -> List[bytes]:
    return [message[:16], message[16:]]


def receive_file_stop_wait(socket_connected, path: str, address, processed):
    with open(path, "wb") as f:
        while True:
            key, datachunk = _get_message_stop_wait(
                socket_connected.recvfrom(BUFFER_SIZE)[0]
            )
            socket_connected.sendto(key, address)
            if key in processed:
                continue
            processed.add(key)
            f.write(datachunk)
            if len(datachunk) < BUFFER_SIZE - len(key):
                break
    logging.info(f"finished receiving and storing file at {path}")


