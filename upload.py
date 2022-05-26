from src.upload.upload_cli import UploadCLI
from src.lib.handler import InterruptHandler
from src.lib.logger import Logger
import logging
import src.upload.upload as upload


if __name__ == "__main__":
    args = UploadCLI().parse_args()
    logger = Logger(args.verbose, args.quiet)
    with InterruptHandler() as handler:
        if args.arquitecture == "select_and_repeat":
            s = upload.UploadSelectAndRepeat(args.host, args.port, args.name)
            handler.listener(s.close)
            s.send()
        elif args.arquitecture == "stop_and_wait":
            s = upload.UploadStopAndWait(args.host, args.port, args.name)  # TO-DO
            handler.listener(s.close)
            s.send()
        else:
            logging.info(
                "ERROR: Invalid arquitecture. Should be select_and_repeat or stop_and_wait"
            )
