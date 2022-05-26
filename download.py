from src.download.download_cli import DownloadCLI
import src.download.download as download
from src.lib.handler import InterruptHandler
from src.lib.logger import Logger
import logging


if __name__ == "__main__":
    args = DownloadCLI().parse_args()
    logger = Logger(args.verbose, args.quiet)
    with InterruptHandler() as handler:
        if args.arquitecture == "select_and_repeat":
            s = download.DownloadSelectAndRepeat(
                args.host, args.port, args.name, args.dst
            )
            s.receive()
        elif args.arquitecture == "stop_and_wait":
            s = download.DownloadStopAndWait(
                args.host, args.port, args.name, args.dst
            )  # TO-DO
            s.receive()
        else:
            logging.info(
                "ERROR: Invalid arquitecture. Should be select_and_repeat or stop_and_wait"
            )
