import archive
import threading
import unittest


def _test_archive_multithreading(arc, id):
    for i in range(id * 100, id * 100 + 1):
        arc.setOwnership(str(i), "hello.txt" + str(i), True)


class ArchiveTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.arc = archive.Archive()

    def tearDown(self):
        self.arc.clear()

    def test_archive_trivial(self):
        assert self.arc.setOwnership("1.1.1.1", "hello.txt", True)

    def test_archive_2Files1IP(self):
        assert self.arc.setOwnership("1.1.1.1", "hello.txt", True)
        assert self.arc.setOwnership("1.1.1.1", "hello2.txt", True)

    def test_archive_2Files2IPs(self):
        assert self.arc.setOwnership("1.1.1.1", "hello.txt", True)
        assert self.arc.setOwnership("1.1.1.2", "hello2.txt", True)

    def test_archive_1File2IPsR(self):
        assert self.arc.setOwnership("1.1.1.1", "hello.txt", False)
        assert self.arc.setOwnership("1.1.1.2", "hello.txt", False)

    def test_archive_1File2IPsW(self):
        assert self.arc.setOwnership("1.1.1.1", "hello.txt", True)
        assert not self.arc.setOwnership("1.1.1.2", "hello.txt", True)

    def test_archive_1File2IPsRW(self):
        assert self.arc.setOwnership("1.1.1.1", "hello.txt", False)
        assert not self.arc.setOwnership("1.1.1.2", "hello.txt", True)

    def test_archive_1File2IPsRW2(self):
        assert self.arc.setOwnership("1.1.1.1", "hello.txt", True)
        assert not self.arc.setOwnership("1.1.1.2", "hello.txt", False)

    def test_archive_releaseW(self):
        assert self.arc.setOwnership("1.1.1.1", "hello.txt", True)
        assert not self.arc.setOwnership("1.1.1.2", "hello.txt", True)
        self.arc.releaseOwnership("1.1.1.1", "hello.txt")
        assert self.arc.setOwnership("1.1.1.2", "hello.txt", True)

    def test_archive_releaseR(self):
        assert self.arc.setOwnership("1.1.1.1", "hello.txt", False)
        assert self.arc.setOwnership("1.1.1.2", "hello.txt", False)
        self.arc.releaseOwnership("1.1.1.1", "hello.txt")
        assert self.arc.setOwnership("1.1.1.3", "hello.txt", False)
        self.arc.releaseOwnership("1.1.1.2", "hello.txt")

    def test_archive_releaseRW(self):
        assert self.arc.setOwnership("1.1.1.1", "hello.txt", True)
        assert not self.arc.setOwnership("1.1.1.2", "hello.txt", False)
        self.arc.releaseOwnership("1.1.1.1", "hello.txt")
        assert self.arc.setOwnership("1.1.1.2", "hello.txt", False)
        self.arc.releaseOwnership("1.1.1.2", "hello.txt")

    def test_archive_releaseRW2(self):
        assert self.arc.setOwnership("1.1.1.1", "hello.txt", False)
        assert not self.arc.setOwnership("1.1.1.2", "hello.txt", True)
        self.arc.releaseOwnership("1.1.1.1", "hello.txt")
        assert self.arc.setOwnership("1.1.1.2", "hello.txt", True)
        self.arc.releaseOwnership("1.1.1.2", "hello.txt")

    def test_archive_releaseRW3(self):
        assert self.arc.setOwnership("1.1.1.1", "hello.txt", False)
        assert self.arc.setOwnership("1.1.1.2", "hello.txt", False)
        assert self.arc.setOwnership("1.1.1.3", "hello.txt", False)
        assert not self.arc.setOwnership("1.1.1.4", "hello.txt", True)
        self.arc.releaseOwnership("1.1.1.1", "hello.txt")
        assert not self.arc.setOwnership("1.1.1.4", "hello.txt", True)
        self.arc.releaseOwnership("1.1.1.2", "hello.txt")
        assert not self.arc.setOwnership("1.1.1.4", "hello.txt", True)
        self.arc.releaseOwnership("1.1.1.3", "hello.txt")
        assert self.arc.setOwnership("1.1.1.4", "hello.txt", True)
        self.arc.releaseOwnership("1.1.1.4", "hello.txt")

    def test_archive_already_owned(self):
        try:
            self.arc.setOwnership("1.1.1.1", "hello.txt", False)
            self.arc.setOwnership("1.1.1.1", "hello.txt", False)
            return False
        except Exception as e:
            return e == "File already owned"

    def test_archive_not_in_archive(self):
        try:
            self.arc.releaseOwnership("1.1.1.1", "hello.txt", False)
            return False
        except Exception as e:
            return e == "File not in Archive"

    def test_archive_not_owned(self):
        try:
            self.arc.setOwnership("1.1.1.1", "hello.txt", False)
            self.arc.releaseOwnership("1.1.1.2", "hello.txt", False)
        except Exception as e:
            return e == "File not owned"

    def test_archive_multithreading(self):
        x = threading.Thread(target=_test_archive_multithreading, args=(self.arc, 0))
        y = threading.Thread(target=_test_archive_multithreading, args=(self.arc, 1))
        z = threading.Thread(target=_test_archive_multithreading, args=(self.arc, 2))
        x.start()
        y.start()
        z.start()
        x.join()
        y.join()
        z.join()

        try:
            for i in range(301):
                self.arc.releaseOwnership(str(i), "hello.txt" + str(i), False)
            return True
        except Exception:
            return False
