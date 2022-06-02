import socket
from io import TextIOWrapper
from typing import Dict
from lib.timer import RepeatingTimer
import lib.protocol as lib_protocol

BUFFER_SIZE = 1024
ENDING_LIMIT = 10  # times to wait for the ack when finishing sending the file


def write_message(key: bytes, message: bytes) -> bytes:
    return key + message


def _send_callback(socket_connected, address, data_to_send, key):
    data = bytes(
        f"{key:{lib_protocol.PADDING}>{lib_protocol.SEQ_LEN}}", lib_protocol.ENCODING
    )
    msg = write_message(data, data_to_send)
    socket_connected.sendto(msg, address)


def send_data(
        timers: Dict[str, RepeatingTimer],
        socket_connected: socket.socket,
        address: str,
        data_to_send: str,
        key: str,
):
    _send_callback(socket_connected, address, data_to_send, key)
    timers[key] = RepeatingTimer(
        lib_protocol.TIMEOUT_TIMER,
        _send_callback,
        socket_connected,
        address,
        data_to_send,
        key,
    )
    timers[key].start()


def read_file(f: TextIOWrapper, key):
    return f.read(BUFFER_SIZE - len(key))

