from lib.upload.upload import Upload
import lib.selective_repeat as selective_repeat


class UploadSelectiveRepeat(Upload):
    def _send(self, addr):
        selective_repeat.send_file(self.client, self.filename, addr)
