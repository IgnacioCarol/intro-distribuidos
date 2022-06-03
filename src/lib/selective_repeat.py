import socket
import heapq
import lib.utils as lib_utils
import lib.protocol as lib_protocol
import logging

FINISH_RECEIVING = 99999999


def encode(key: int):
    # ToDo: cambiar para el ultimo paquete que se envia
    return f"{key:{lib_protocol.PADDING}>{lib_protocol.SEQ_LEN}}"


def send_file(socket_connected: socket.socket, filename: str, address: str):
    eof_counter = 0
    error_flag = False
    with open(filename, "rb") as f:

        # Revive ACK from server
        logging.info("Starting send with selective repeat...")

        # Initialize timers dict
        timers = {}

        # Firstly, I send data WINDOW_SIZE times
        last_chunk_sent = 0
        key = encode(last_chunk_sent)
        data_to_send = lib_utils.read_file(f, key)
        while data_to_send and last_chunk_sent < lib_protocol.WINDOW_SIZE:
            logging.info("Sending: \n\tdata: {}\n\tkey:{}".format(data_to_send, key))
            lib_utils.send_data(timers, socket_connected, address, data_to_send, key)
            last_chunk_sent += 1
            key = encode(last_chunk_sent)
            data_to_send = lib_utils.read_file(f, key)

        # Then ...
        ack = ""
        while len(timers):
            try:
                # Receive ack from server and cancel all the timers of the received data
                ack, address = socket_connected.recvfrom(lib_utils.BUFFER_SIZE)
                ack_value = str(ack, lib_protocol.ENCODING)
                if ack_value not in timers.keys():
                    continue
                eof_counter = 0
                timers.pop(ack_value).cancel()
                min_ack = int(min(timers.keys())) if len(timers) else last_chunk_sent
                window_shifts = last_chunk_sent - min_ack + 1
                if window_shifts < lib_protocol.WINDOW_SIZE and data_to_send:
                    displacements = (
                        lib_protocol.WINDOW_SIZE + last_chunk_sent - window_shifts
                    )
                    for i in range(last_chunk_sent, displacements):
                        logging.info(f"Sending: \n\tdata: {data_to_send}\n\tkey:{key}")
                        lib_utils.send_data(
                            timers, socket_connected, address, data_to_send, key
                        )
                        last_chunk_sent += 1
                        key = encode(last_chunk_sent)
                        data_to_send = lib_utils.read_file(f, key)
                        if not data_to_send:
                            break

            except socket.timeout:

                # If one socket timed out
                if eof_counter > lib_utils.ENDING_LIMIT:
                    logging.info(
                        f"Timeout: socket tried {lib_utils.ENDING_LIMIT} "
                        f"times to receive an ACK and will not try again"
                    )
                    error_flag = True
                    break
                elif len(ack) < lib_utils.BUFFER_SIZE - len(key):
                    logging.info(
                        f"Timeout: socket tried {eof_counter} times "
                        f"to receive an ACK."
                    )
                    eof_counter += 1
                else:
                    eof_counter += 1
                    logging.info("Timeout: socket did not receive data.")

        eof_counter = 0
        if not error_flag:
            logging.info(f"Finished sending file {filename}")
        while not error_flag:
            try:
                socket_connected.sendto(
                    bytes(f"{FINISH_RECEIVING}", lib_protocol.ENCODING), address
                )
                socket_connected.recvfrom(lib_utils.BUFFER_SIZE)
                break
            except socket.timeout:
                if eof_counter > lib_utils.ENDING_LIMIT:
                    logging.info(
                        f"Timeout: socket tried {lib_utils.ENDING_LIMIT} "
                        f"times to receive an ACK and will not try again"
                    )
                    break
                elif len(ack) < lib_utils.BUFFER_SIZE - len(key):
                    logging.info(
                        f"Timeout: socket tried {eof_counter} times "
                        f"to receive an ACK."
                    )
                    eof_counter += 1
                else:
                    eof_counter += 1
                    logging.info("Timeout: socket did not receive data.")


def _get_message(message: bytes):
    return [int(message[: lib_protocol.SEQ_LEN]), message[lib_protocol.SEQ_LEN :]]


def receive_file(socket_connected, path: str, address):
    logging.info("Starting receive with selective repeat...")

    recv_buffer = []
    heapq.heapify(recv_buffer)

    logging.info("Starting receiving...")
    wanted_seq_number = 0
    seq_number = 0
    error_counter = 0
    with open(path, "wb") as f:
        while seq_number != FINISH_RECEIVING:
            try:
                seq_number, datachunk = _get_message(
                    socket_connected.recvfrom(lib_utils.BUFFER_SIZE)[0]
                )
                error_counter = 0
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
                    while (
                        len(recv_buffer) > 0 and recv_buffer[0][0] == wanted_seq_number
                    ):
                        f.write(heapq.heappop(recv_buffer)[1])
                        wanted_seq_number = wanted_seq_number + 1
            except socket.timeout as e:
                logging.info("Timeout")
                error_counter += 1
                if error_counter > 3:
                    logging.error(
                        f"more than {error_counter - 1} timeouts, aborting execution"
                    )
                    raise e
                continue

            logging.info(
                "Sending ack with wanted sequence number: {}.".format(seq_number)
            )
            key = bytes(
                encode(seq_number),
                lib_protocol.ENCODING,
            )
            socket_connected.sendto(key, address)

    logging.info("finished receiving and storing file at {}".format(path))
