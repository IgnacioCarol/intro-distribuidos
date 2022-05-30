import socket
import heapq
import os
from io import TextIOWrapper
from typing import List, Dict
from lib.timer import RepeatingTimer
import lib.protocol as lib_protocol
import logging

BUFFER_SIZE = 1024
ENDING_LIMIT = 10  # times to wait for the ack when finishing sending the file


def encode_selective_repeat(key: int):
    return f"{key:{lib_protocol.PADDING}>{lib_protocol.SEQ_LEN}}"


def write_message(key: bytes, message: bytes) -> bytes:
    return key + message


def _send_callback(socket_connected, address, data_to_send, key):
    data = bytes(
        f"{key:{lib_protocol.PADDING}>{lib_protocol.SEQ_LEN}}", lib_protocol.ENCODING
    )
    msg = write_message(data, data_to_send)
    socket_connected.sendto(msg, address)


def _send_data(
        timers: Dict[int, RepeatingTimer],
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


def send_file_selective_repeat(
        socket_connected: socket.socket, filename: str, address: str
):
    eof_counter = 0

    with open(filename, "rb") as f:

        # Revive ACK from server
        logging.info("Starting send with select and repeat...")

        file_size = os.stat(filename).st_size
        while True:
            try:

                logging.info("Sending ACK...")
                ack = bytes(
                    lib_protocol.MSG_FILE_SIZE + encode_selective_repeat(file_size),
                    lib_protocol.ENCODING,
                )
                socket_connected.sendto(ack, address)

                logging.info("Receiving SYNC-ACK...")
                sync_ack = str(
                    socket_connected.recvfrom(BUFFER_SIZE)[0], lib_protocol.ENCODING
                )

                if sync_ack == lib_protocol.MSG_FILE_SIZE_ACK:
                    logging.info("Received ACK.")
                    break

            except socket.timeout:
                logging.info("Timeout: no ACK SYNC received.")
                return

        # Initialize timers dict
        timers = {}

        # Firstly, I send data WINDOW_SIZE times
        last_chunk_sent = 0
        key = encode_selective_repeat(last_chunk_sent)
        data_to_send = read_file(f, key)
        while data_to_send and last_chunk_sent < lib_protocol.WINDOW_SIZE:
            logging.info("Sending: \n\tdata: {}\n\tkey:{}".format(data_to_send, key))
            _send_data(timers, socket_connected, address, data_to_send, key)
            last_chunk_sent += 1
            key = encode_selective_repeat(last_chunk_sent)
            data_to_send = read_file(f, key)

        # Then ...
        latest_ack = 0
        while data_to_send:
            try:
                # Receive ack from server and cancel all the timers of the recieved data
                ack, address = socket_connected.recvfrom(BUFFER_SIZE)
                ack = int(ack)
                timers.pop(ack)
                min_ack = min(timers.keys())
                window_shifts = last_chunk_sent - min_ack + 1
                if window_shifts < lib_protocol.WINDOW_SIZE:
                    displacements = \
                        lib_protocol.WINDOW_SIZE \
                        + last_chunk_sent \
                        - window_shifts
                    for i in range(last_chunk_sent, displacements):
                        logging.info(
                            "Sending: \n\tdata: {}\n\tkey:{}".format(data_to_send, key)
                        )
                        _send_data(timers, socket_connected, address, data_to_send, key)
                        last_chunk_sent += 1
                        key = encode_selective_repeat(last_chunk_sent)
                        data_to_send = read_file(f, key)

            except socket.timeout:

                # If one socket timed out
                if eof_counter > ENDING_LIMIT:
                    logging.info(
                        "Timeout: socket tried {} times to receive an ACK and will not try again".format(
                            ENDING_LIMIT
                        )
                    )
                    break
                elif len(ack) < BUFFER_SIZE - len(key):
                    logging.info(
                        "Timeout: socket tried {} times to receive an ACK.".format(
                            eof_counter
                        )
                    )
                    eof_counter += 1
                else:
                    eof_counter += 1
                    logging.info("Timeout: socket did not receive data.")


def read_file(f: TextIOWrapper, key):
    return f.read(BUFFER_SIZE - len(key))


def _get_message_selective_repeat(message: bytes):
    return [int(message[: lib_protocol.SEQ_LEN]), message[lib_protocol.SEQ_LEN:]]


def receive_file_selective_repeat(socket_connected, path: str, address):
    logging.info("Starting receive with select and repeat...")

    recv_buffer = []
    heapq.heapify(recv_buffer)

    # Receive file size and send ACK
    logging.info("Receiving file length...")
    while True:
        try:
            datachunk = socket_connected.recvfrom(BUFFER_SIZE)[0]
            logging.info("Received a datachunk: {}".format(datachunk))
            if datachunk[: len(lib_protocol.MSG_FILE_SIZE)] == bytes(
                    lib_protocol.MSG_FILE_SIZE, lib_protocol.ENCODING
            ):
                len_msg = len(lib_protocol.MSG_FILE_SIZE)
                file_size = int(
                    datachunk[len_msg: len_msg + lib_protocol.SEQ_LEN]
                )
                logging.info("File length received: {}".format(file_size))
                socket_connected.sendto(
                    bytes(lib_protocol.MSG_FILE_SIZE_ACK, lib_protocol.ENCODING),
                    address,
                )
                break
        except socket.timeout:
            logging.info("Timeout: File length not received.")
            return

    logging.info("Starting receiving...")
    wanted_seq_number = 0
    with open(path, "wb") as f:
        while wanted_seq_number * lib_protocol.CHUNK_SIZE < file_size:
            try:
                seq_number, datachunk = _get_message_selective_repeat(
                    socket_connected.recvfrom(BUFFER_SIZE)[0]
                )
                logging.info(
                    "Receiving:\n\tkey: {}\n\tdata: {}".format(seq_number, datachunk)
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
                encode_selective_repeat(wanted_seq_number),
                lib_protocol.ENCODING,
            )
            socket_connected.sendto(key, address)

    logging.info("finished receiving and storing file at {}".format(path))
