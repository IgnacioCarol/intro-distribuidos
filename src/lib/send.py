import socket
import uuid
import heapq
import os
from io import TextIOWrapper
from msilib.schema import File
from time import sleep
from typing import List
from lib.timer import RepeatingTimer
from protocol import *

BUFFER_SIZE = 1024
ENDING_LIMIT = 10  # times to wait for the ack when finishing sending the file


def write_message(key: bytes, message: bytes) -> bytes:
    return key + message


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
                if len(msg) < BUFFER_SIZE - len(key):
                    eof_counter += 1
                print("timeouteo")
                continue
            key = uuid.uuid4().bytes
            data_to_send = read_file(f, key)


def _send_callback(socket_connected, address, data_to_send, key):
    data = bytes(f'{key:{PADDING}>{SEQ_LEN}}', ENCODING)
    msg = write_message(data, data_to_send)
    socket_connected.sendto(msg, address)

def _send_data(timers: List[RepeatingTimer], socket_connected: socket.socket, address: str, data_to_send: str, last_chunk_sent: int):
    _send_callback(socket_connected, address, data_to_send, last_chunk_sent)
    timers.append(RepeatingTimer(TIMEOUT_TIMER, _send_callback, [socket_connected, address, data_to_send, last_chunk_sent]))
    timers[-1].start()

def send_file_select_and_repeat(socket_connected: socket.socket, filename: str, address: str):
#   socket_connected.setblocking(False)
    with open(filename, "rb") as f:
        timers = []
        last_chunk_sent = 0
        latest_ack = 0
        data_to_send = read_file(f, last_chunk_sent)
        
        #To do: Put this logic in the conneciton ack (watchout infinite cycle)
        while True:
            try:
                msg = bytes(MSG_FILE_SIZE + str(os.stat(file_name).size()), ENCODING)
                socket_connected.sendto(msg, address)
                datachunk = socket_connected.recvfrom(BUFFER_SIZE)[0]
                if(datachunk == MSG_FILE_SIZE_ACK)
                    break
            except socket.timeout:
                print("timeouteo")

        while data_to_send and last_chunk_sent < WINDOW_SIZE:
            _send_data(timers, socket_connected, address, data_to_send, last_chunk_sent)
            data_to_send = read_file(f, last_chunk_sent)
            last_chunk_sent += 1

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
                print("timeouteo")

            for i in range(WINDOW_SIZE - len(timers)):
                _send_data(timers, socket_connected, address, data_to_send, last_chunk_sent)
                data_to_send = read_file(f, last_chunk_sent)
                last_chunk_sent += 1

def read_file(f: TextIOWrapper, key):
    return f.read(BUFFER_SIZE - len(key))

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
            if len(datachunk) < BUFFER_SIZE - len(key):
                break
    print(f"finished receiving and storing file at {path}")

def _get_message_select_and_repeat(message: bytes):
    return [int(message[:SEQ_LEN]), message[SEQ_LEN:]]

def receive_file_select_and_repeat(socket_connected, path: str, address, processed):
    wanted_seq_number = 0
    recv_buffer = []
    file_len = 0 
    heapq.heapify(recv_buffers)

    while True:
        #To do: Put this logic in the conneciton ack
        try:
            datachunk = socket_connected.recvfrom(BUFFER_SIZE)[0]
            if(datachunk[:len(MSG_FILE_SIZE)] == MSG_FILE_SIZE):
                file_len = int(datachunk[len(MSG_FILE_SIZE):])/CHUNK_SIZE
                socket_connected.sendto(bytes(MSG_FILE_SIZE_ACK, ENCODING), address)
        except socket.timeout:
            print("timeouteo")
            return

    while data_to_send:
        sleep(5)
        msg = write_message(key, data_to_send)
        socket_connected.sendto(msg, address)

    with open(path, "wb") as f:
        while wanted_seq_number <= file_len:
            try:
                seq_number, datachunk = _get_message_select_and_repeat(socket_connected.recvfrom(BUFFER_SIZE)[0])
                if (seq_number > wanted_seq_number and len(recv_buffer) <= WINDOW_SIZE):
                   if not next((True for x in recv_buffer if x[0] == seq_number), False):
                        heapq.heappush(recv_buffer, (seq_number, datachunk))
                elif (seq_number == wanted_seq_number):
                    f.write(datachunk)
                    wanted_seq_number = seq_number + 1
                    while(len(recv_buffer) > 0 and recv_buffer[0] == wanted_seq_number):
                        f.write(heapq.heappop(recv_buffers)[1])
                        wanted_seq_number = seq_number + 1
            except socket.timeout:
                print("timeouteo")
            key = bytes(f'{wanted_seq_number:{PADDING}>{SEQ_LEN}}', ENCODING)
            socket_connected.sendto(key, address)
    print(f"finished receiving and storing file at {path}")