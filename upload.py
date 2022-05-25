from src.upload.upload_cli import UploadCLI
from src.upload.upload import Upload
from src.lib.handler import InterruptHandler

if __name__ == "__main__":
    args = UploadCLI().parse_args()
    with InterruptHandler() as handler:
        s = Upload(args.host, args.port, args.name)
        handler.listener(s.close)
        s.send()
