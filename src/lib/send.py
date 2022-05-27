import socket
import uuid
import heapq
import os
from io import TextIOWrapper
from typing import List
from lib.timer import RepeatingTimer
import lib.protocol as lib_protocol
import logging
import math

BUFFER_SIZE = 1024
ENDING_LIMIT = 10  # times to wait for the ack when finishing sending the file


def encode_select_and_repeat(key: int):
    return f"{key:{lib_protocol.PADDING}>{lib_protocol.SEQ_LEN}}"


def decode_select_and_repeat(key: int):
    return int(key)


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


def send_file_select_and_repeat(
    socket_connected: socket.socket, filename: str, address: str
):
    eof_counter = 0

    with open(filename, "rb") as f:

        # Revieve ACk from server
        logging.info("Starting send with select and repeat...")

        file_size = os.stat(filename).st_size
        while True:
            try:

                logging.info("Sending ACK...")
                ack = bytes(
                    lib_protocol.MSG_FILE_SIZE + encode_select_and_repeat(file_size),
                    lib_protocol.ENCODING,
                )
                socket_connected.sendto(ack, address)

                logging.info("Recieving SYNC-ACK...")
                sync_ack = str(
                    socket_connected.recvfrom(BUFFER_SIZE)[0], lib_protocol.ENCODING
                )

                if sync_ack == lib_protocol.MSG_FILE_SIZE_ACK:
                    logging.info("Recieved ACK.")
                    break

            except socket.timeout:
                logging.info("Timeout: no ACK SYNC recieved.")
                return

        # Initialize timers list
        timers = []

        # Firstly, I send data WINDOW_SIZE times
        last_chunk_sent = 0
        key = encode_select_and_repeat(last_chunk_sent)
        data_to_send = read_file(f, key)
        while data_to_send and last_chunk_sent < lib_protocol.WINDOW_SIZE:
            logging.info("Sending: \n\tdata: {}\n\tkey:{}".format(data_to_send, key))
            _send_data(timers, socket_connected, address, data_to_send, key)
            last_chunk_sent += 1
            key = encode_select_and_repeat(last_chunk_sent)
            data_to_send = read_file(f, key)

        # Then ...
        latest_ack = 0
        while data_to_send:
            try:
                # Recieve ack from server and cancel all the timers of the recieved data
                ack, adress = socket_connected.recvfrom(BUFFER_SIZE)
                ack = decode_select_and_repeat(ack)
                for i in range(latest_ack, ack + 1):
                    timers[i].cancel()
                    timers.pop(i)
                latest_ack = ack + 1

            except socket.timeout:

                # If one socket timed out
                if eof_counter > ENDING_LIMIT:
                    logging.info(
                        "Timeout: socket tried {} times to recieve an ACK and will not try again".format(
                            ENDING_LIMIT
                        )
                    )
                    break
                elif len(ack) < BUFFER_SIZE - len(key):
                    logging.info(
                        "Timeout: socket tried {} times to recieve an ACK.".format(
                            eof_counter
                        )
                    )
                    eof_counter += 1
                else:
                    eof_counter += 1
                    logging.info("Timeout: socket did not recieve data.")

            for i in range(lib_protocol.WINDOW_SIZE - len(timers)):
                logging.info(
                    "Sending: \n\tdata: {}\n\tkey:{}".format(data_to_send, key)
                )
                _send_data(timers, socket_connected, address, data_to_send, key)
                last_chunk_sent += 1
                key = encode_select_and_repeat(last_chunk_sent)
                data_to_send = read_file(f, key)


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

    logging.info("Starting recieve with select and repeat...")

    recv_buffer = []
    heapq.heapify(recv_buffer)

    # Recieve file size and send ACK
    file_size = 0
    logging.info("Recieving file length...")
    while True:
        try:
            datachunk = socket_connected.recvfrom(BUFFER_SIZE)[0]
            logging.info("Recieved a datachunk: {}".format(datachunk))
            if datachunk[: len(lib_protocol.MSG_FILE_SIZE)] == bytes(
                lib_protocol.MSG_FILE_SIZE, lib_protocol.ENCODING
            ):
                len_msg = len(lib_protocol.MSG_FILE_SIZE)
                file_size = decode_select_and_repeat(
                    datachunk[len_msg : len_msg + lib_protocol.SEQ_LEN]
                )
                logging.info("File legnth recieved: {}".format(file_size))
                socket_connected.sendto(
                    bytes(lib_protocol.MSG_FILE_SIZE_ACK, lib_protocol.ENCODING),
                    address,
                )
                break
        except socket.timeout:
            logging.info("Timeout: File legnth not recieved.")
            return

    logging.info("Starting recieving...")
    wanted_seq_number = 0
    amout_of_chunks = math.ceil(file_size / lib_protocol.CHUNK_SIZE) - 1
    with open(path, "wb") as f:
        while wanted_seq_number < amout_of_chunks:
            try:
                seq_number, datachunk = _get_message_select_and_repeat(
                    socket_connected.recvfrom(BUFFER_SIZE)[0]
                )
                logging.info(
                    "Recieving:\n\tkey: {}\n\tdata: {}".format(seq_number, datachunk)
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
                logging.info("Timeout")

            logging.info(
                "Sending ack with wanted sequence number: {}.".format(wanted_seq_number)
            )
            key = bytes(
                encode_select_and_repeat(wanted_seq_number),
                lib_protocol.ENCODING,
            )
            socket_connected.sendto(key, address)

    logging.info("finished receiving and storing file at {}".format(path))
