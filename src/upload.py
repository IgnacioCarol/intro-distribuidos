from lib.upload.upload import UploadSelectiveRepeat, UploadStopAndWait
from lib.upload.upload_cli import UploadCLI
from lib.handler import InterruptHandler
from lib.logger import Logger
import logging

if __name__ == "__main__":
    args = UploadCLI().parse_args()
    logger = Logger(args.verbose, args.quiet)
    with InterruptHandler() as handler:
        if args.arquitecture == "select_and_repeat":
            s = UploadSelectiveRepeat(args.host, args.port, args.name)
            handler.listener(s.close)
            s.send()
        elif args.arquitecture == "stop_and_wait":
            s = UploadStopAndWait(args.host, args.port, args.name) 
            handler.listener(s.close)
            s.send()
        else:
            logging.info(
                "ERROR: Invalid arquitecture. Should be select_and_repeat or stop_and_wait"
            )
