import os
from lib.download.download import Download
import lib.selective_repeat as selective_repeat


class DownloadSelectiveRepeat(Download):
    def _receive(self, addr):
        file_path = "{}/{}".format(os.getcwd(), self.filename)
        return selective_repeat.receive_file(self.client, file_path, addr)