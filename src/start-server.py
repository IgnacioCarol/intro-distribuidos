from lib.start_server.start_server_cli import StartServerCLI
from lib.handler import InterruptHandler
from lib.logger import Logger
from lib.start_server.start_server import ServerSelectiveRepeat, ServerStopAndWait
import logging

if __name__ == "__main__":
    args = StartServerCLI().parse_args()
    logger = Logger(args.verbose, args.quiet)
    with InterruptHandler() as handler:
        if args.arquitecture == "select_and_repeat":
            logging.info("[server] Arquitecture select and repeat")
            s = ServerSelectiveRepeat(args.host, args.port, args.storage)
            handler.listener(s.close)
            s.listen()
        elif args.arquitecture == "stop_and_wait":
            logging.info("[server] Arquitecture stop and wait")
            s = ServerStopAndWait(args.host, args.port, args.storage)
            handler.listener(s.close)
            s.listen()
        else:
            logging.info(
                "ERROR: Invalid arquitecture. Should be select_and_repeat or stop_and_wait"
            )
