import socket
import heapq
import os
import src.lib.utils as lib_utils
import src.lib.protocol as lib_protocol
import logging


def encode(key: int):
    # ToDo: cambiar para el ultimo paquete que se envia
    return f"{key:{lib_protocol.PADDING}>{lib_protocol.SEQ_LEN}}"


def send_file(
        socket_connected: socket.socket, filename: str, address: str
):
    eof_counter = 0

    with open(filename, "rb") as f:

        # Revive ACK from server
        logging.info("Starting send with selective repeat...")

        file_size = os.stat(filename).st_size
        while True:
            try:

                logging.info("Sending ACK...")
                ack = bytes(
                    lib_protocol.MSG_FILE_SIZE + encode(file_size),
                    lib_protocol.ENCODING,
                )
                socket_connected.sendto(ack, address)

                logging.info("Receiving SYNC-ACK...")
                sync_ack = str(
                    socket_connected.recvfrom(lib_utils.BUFFER_SIZE)[0],
                    lib_protocol.ENCODING
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
        key = encode(last_chunk_sent)
        data_to_send = lib_utils.read_file(f, key)
        while data_to_send and last_chunk_sent < lib_protocol.WINDOW_SIZE:
            logging.info("Sending: \n\tdata: {}\n\tkey:{}".format(data_to_send, key))
            lib_utils.send_data(timers, socket_connected, address, data_to_send, key)
            last_chunk_sent += 1
            key = encode(last_chunk_sent)
            data_to_send = lib_utils.read_file(f, key)

        # Then ...
        while data_to_send:
            try:
                # Receive ack from server and cancel all the timers of the received data
                ack, address = socket_connected.recvfrom(lib_utils.BUFFER_SIZE)
                ack = int(ack)
                timers.pop(ack)
                min_ack = min(timers.keys())
                window_shifts = last_chunk_sent - min_ack + 1
                # Si se mando todo, como hago para cortar? me tengo que quedar en este while, no puedo seguir iterando
                # tengo que recibir cierta cantidad de veces que se termino de mandar, tengo que tener cuidado
                # si recibo algo que no es int y lo quiero pasar a int, ahi revienta
                if window_shifts < lib_protocol.WINDOW_SIZE:
                    displacements = \
                        lib_protocol.WINDOW_SIZE \
                        + last_chunk_sent \
                        - window_shifts
                    for i in range(last_chunk_sent, displacements):
                        logging.info(
                            f"Sending: \n\tdata: {data_to_send}\n\tkey:{key}"
                        )
                        lib_utils.send_data(timers, socket_connected, address, data_to_send, key)
                        last_chunk_sent += 1
                        # ToDo: mandar el ack nomas, o no se que me mandan ellos la verdad
                        key = encode(last_chunk_sent)
                        data_to_send = lib_utils.read_file(f, key)

            except socket.timeout:

                # If one socket timed out
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
    return [int(message[: lib_protocol.SEQ_LEN]), message[lib_protocol.SEQ_LEN:]]


def receive_file(socket_connected, path: str, address):
    logging.info("Starting receive with selective repeat...")

    recv_buffer = []
    heapq.heapify(recv_buffer)

    # Receive file size and send ACK
    logging.info("Receiving file length...")
    while True:
        try:
            datachunk = socket_connected.recvfrom(lib_utils.BUFFER_SIZE)[0]
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
                seq_number, datachunk = _get_message(
                    socket_connected.recvfrom(lib_utils.BUFFER_SIZE)[0]
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
                encode(wanted_seq_number),
                lib_protocol.ENCODING,
            )
            socket_connected.sendto(key, address)

    logging.info("finished receiving and storing file at {}".format(path))
