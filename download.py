from src.download.download_cli import DownloadCLI
from src.download.download import Download
from src.lib.handler import InterruptHandler

if __name__ == "__main__":
    args = DownloadCLI().parse_args()
    with InterruptHandler() as handler:
        s = Download(args.host, args.port, args.name, args.dst)
        s.receive()
