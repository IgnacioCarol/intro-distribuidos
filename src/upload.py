import logging
import os

from lib.handler import InterruptHandler
from lib.logger import Logger
from lib.upload.upload_cli import UploadCLI
from lib.upload.upload_selective_repeat import UploadSelectiveRepeat
from lib.upload.upload_stop_and_wait import UploadStopAndWait

if __name__ == "__main__":
    args = UploadCLI().parse_args()
    logger = Logger(args.verbose, args.quiet)
    with InterruptHandler() as handler:
        if not os.path.isdir(args.src) or not os.path.isfile(f"{args.src}/{args.name}"):
            logging.error(f"file {args.src}/{args.name} does not exist")
        elif args.arquitecture == "select_and_repeat":
            logging.info("[server] Arquitecture select and repeat")
            s = UploadSelectiveRepeat(args.host, args.port, args.name, args.src)
            handler.listener(s.close)
            s.send()
        elif args.arquitecture == "stop_and_wait":
            logging.info("[server] Arquitecture stop and wait")
            s = UploadStopAndWait(args.host, args.port, args.name, args.src)
            handler.listener(s.close)
            s.send()
        else:
            logging.error(
                "ERROR: Invalid arquitecture. Should be select_and_repeat or stop_and_wait"
            )
