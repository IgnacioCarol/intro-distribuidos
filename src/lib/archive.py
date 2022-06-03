import threading as th

from typing import Dict, Set, Tuple


class FileAlreadyOwnedError(Exception):
    pass


class FileNotInArchiveError(Exception):
    pass


class FileNotOwnedError(Exception):
    pass


class Archive:
    """This class implements a system that keeps track of files in use by a clients"""

    lock = th.Lock()
    ip_by_file: Dict[
        str, Tuple[Set[str], int, bool]
    ] = {}  # key: filename, value : ({ownerips}, rcount, bool)

    def set_ownership(self, ip, file_name, w):
        self.lock.acquire()
        try:
            ips, amount, is_writing = self.ip_by_file.get(file_name, (set(), 0, False))
            if ip in ips:
                raise FileAlreadyOwnedError()
            if is_writing or (w and amount != 0):
                return False
            ips.add(ip)
            self.ip_by_file[file_name] = (ips, amount + 1, w)
        finally:
            self.lock.release()
        return True

    def release_ownership(self, ip, file_name):
        self.lock.acquire()
        try:
            if file_name not in self.ip_by_file:
                raise FileNotInArchiveError()
            ips, amount, is_writing = self.ip_by_file.get(file_name, (set(), 0, False))
            if ip not in ips:
                raise FileNotOwnedError()
            ips.remove(ip)
            self.ip_by_file[file_name] = (ips, amount - 1, False)
        finally:
            self.lock.release()

    def clear(self):
        self.lock.acquire()
        self.ip_by_file.clear()
        self.lock.release()
