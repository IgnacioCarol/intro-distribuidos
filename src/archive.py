import threading as th


class Archive:
    """This class implements a sistem that keeps track of files in use by a clients"""

    lock = th.Lock()
    ip_by_file = {}  # key: filename, value : ([ownerips], rcount)

    def setOwnership(self, ip, file_name, w):
        self.lock.acquire()
        if file_name in self.ip_by_file:
            tup = self.ip_by_file[file_name]
            if ip in tup[0]:
                self.lock.release()
                raise Exception("File already owned")
            if w or tup[1] == -1:
                self.lock.release()
                return False
            tup[0].add(ip)
            self.ip_by_file[file_name] = (tup[0], tup[1] + 1)
        else:
            self.ip_by_file[file_name] = (set({ip}), -1 if w else 1)
        self.lock.release()
        return True

    def releaseOwnership(self, ip, file_name):
        self.lock.acquire()
        if file_name not in self.ip_by_file:
            self.lock.release()
            raise Exception("File not in Archive")
        tup = self.ip_by_file[file_name]
        if ip not in tup[0]:
            self.lock.release()
            raise Exception("File not owned")
        if tup[1] <= 1:
            del self.ip_by_file[file_name]
        else:
            tup[0].remove(ip)
            self.ip_by_file[file_name] = (tup[0], tup[1] - 1)
        self.lock.release()

    def clear(self):
        self.lock.acquire()
        self.ip_by_file.clear()
        self.lock.release()
