import socket
import uuid
import heapq
import os
from math import ceil
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
    last_chunk_sent: int,
):
    _send_callback(socket_connected, address, data_to_send, last_chunk_sent)
    timers.append(
        RepeatingTimer(
            lib_protocol.TIMEOUT_TIMER,
            _send_callback,
            [socket_connected, address, data_to_send, last_chunk_sent],
        )
    )
    timers[-1].start()


def send_file_select_and_repeat(
    socket_connected: socket.socket, filename: str, address: str
):
    eof_counter = 0
    #   socket_connected.setblocking(False)
    with open(filename, "rb") as f:
        timers = []
        last_chunk_sent = 0
        latest_ack = 0
        data_to_send = read_file(f, last_chunk_sent)

        # To do: Put this logic in the conneciton ack (watchout infinite cycle)
        while True:
            try:
                msg = bytes(
                    lib_protocol.MSG_FILE_SIZE + str(os.stat(filename).size()),
                    lib_protocol.ENCODING,
                )
                print(msg)
                socket_connected.sendto(msg, address)
                datachunk = str(
                    socket_connected.recvfrom(BUFFER_SIZE)[0], lib_protocol.ENCODING
                )
                if datachunk == lib_protocol.MSG_FILE_SIZE_ACK:
                    break
            except socket.timeout:
                print("send timeout")

        print("comienzo a mandar")
        while data_to_send and last_chunk_sent < lib_protocol.WINDOW_SIZE:
            _send_data(timers, socket_connected, address, data_to_send, last_chunk_sent)
            data_to_send = read_file(f, last_chunk_sent)
            last_chunk_sent += 1

        key, data_to_send = [b"esto estaba sin definirrr", b"esto estaba sin definirrr"]
        while data_to_send:
            try:
                ack, address = socket_connected.recvfrom(BUFFER_SIZE)
                ack = int(ack)
                for i in range(latest_ack, ack):
                    timers[i].cancel()
                    timers.pop(i)

                latest_ack = ack - 1
            except socket.timeout:
                if eof_counter > ENDING_LIMIT:
                    break
                if len(msg) < BUFFER_SIZE - len(key):
                    eof_counter += 1
                logging.info("send timeout")

            for i in range(lib_protocol.WINDOW_SIZE - len(timers)):
                _send_data(
                    timers, socket_connected, address, data_to_send, last_chunk_sent
                )
                data_to_send = read_file(f, last_chunk_sent)
                last_chunk_sent += 1


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
    print(f"finished receiving and storing file at {path}")


def _get_message_select_and_repeat(message: bytes):
    return [int(message[: lib_protocol.SEQ_LEN]), message[lib_protocol.SEQ_LEN :]]


def receive_file_select_and_repeat(socket_connected, path: str, address, processed):
    wanted_seq_number = 0
    recv_buffer = []
    file_len = 0

    heapq.heapify(recv_buffer)

    while True:
        # To do: Put this logic in the conneciton ack
        try:
            datachunk = socket_connected.recvfrom(BUFFER_SIZE)[0]
            print(datachunk)
            if datachunk[: len(lib_protocol.MSG_FILE_SIZE)] == bytes(
                lib_protocol.MSG_FILE_SIZE, lib_protocol.ENCODING
            ):
                datachunk = int(datachunk[len(lib_protocol.MSG_FILE_SIZE) :])
                file_len = ceil(datachunk / lib_protocol.CHUNK_SIZE)
                socket_connected.sendto(
                    bytes(lib_protocol.MSG_FILE_SIZE_ACK, lib_protocol.ENCODING),
                    address,
                )
                break
        except socket.timeout:
            print("recieve timeout")
            return

    print("comienzo a recibir")

    key, data_to_send = [b"esto estaba sin definirrr", b"esto estaba sin definirrr"]
    while data_to_send:
        # sleep(5)
        msg = write_message(key, data_to_send)
        socket_connected.sendto(msg, address)

    with open(path, "wb") as f:
        while wanted_seq_number <= file_len:
            try:
                seq_number, datachunk = _get_message_select_and_repeat(
                    socket_connected.recvfrom(BUFFER_SIZE)[0]
                )
                if (
                    seq_number > wanted_seq_number
                    and len(recv_buffer) <= lib_protocol.WINDOW_SIZE
                ):
                    if not next(
                        (True for x in recv_buffer if x[0] == seq_number), False
                    ):
                        heapq.heappush(recv_buffer, (seq_number, datachunk))
                elif seq_number == wanted_seq_number:
                    f.write(datachunk)
                    wanted_seq_number = seq_number + 1
                    while len(recv_buffer) > 0 and recv_buffer[0] == wanted_seq_number:
                        f.write(heapq.heappop(recv_buffer)[1])
                        wanted_seq_number = seq_number + 1
            except socket.timeout:
                logging.info("recieve timeout")
            key = bytes(
                f"{wanted_seq_number:{lib_protocol.PADDING}>{lib_protocol.SEQ_LEN}}",
                lib_protocol.ENCODING,
            )
            socket_connected.sendto(key, address)
    print(f"finished receiving and storing file at {path}")
