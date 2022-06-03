from lib.upload.upload import Upload
import lib.selective_repeat as stop_and_wait

class UploadStopAndWait(Upload):
    def _send(self, addr):
        stop_and_wait.send_file(self.client, self.filename, addr)