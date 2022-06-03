import os.path

from lib.download.download_cli import DownloadCLI
from lib.download.download_selective_repeat import DownloadSelectiveRepeat
from lib.download.download_stop_and_wait import DownloadStopAndWait
from lib.handler import InterruptHandler
from lib.logger import Logger
import logging


if __name__ == "__main__":
    args = DownloadCLI().parse_args()
    logger = Logger(args.verbose, args.quiet)
    with InterruptHandler() as handler:
        if not os.path.isdir(args.dst):
            logging.error(f"path {args.dst} does not exist")
        elif args.arquitecture == "select_and_repeat":
            logging.info("[server] Arquitecture select and repeat")
            s = DownloadSelectiveRepeat(args.host, args.port, args.name, args.dst)
            handler.listener(s.close)
            s.receive()
        elif args.arquitecture == "stop_and_wait":
            logging.info("[server] Arquitecture stop and wait")
            s = DownloadStopAndWait(args.host, args.port, args.name, args.dst)
            handler.listener(s.close)
            s.receive()
        else:
            logging.error(
                "ERROR: Invalid arquitecture. Should be select_and_repeat or stop_and_wait"
            )
