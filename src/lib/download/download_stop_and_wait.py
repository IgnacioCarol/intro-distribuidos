from lib.download.download import Download
import lib.stop_wait as stop_and_wait


class DownloadStopAndWait(Download):
    def _receive(self, addr):
        file_path = "{}/{}".format(self.path, self.filename)
        return stop_and_wait.receive_file(self.client, file_path, addr, set())
