from src.start_server.start_server_cli import StartServerCLI
import src.start_server.start_server as server
from src.lib.handler import InterruptHandler
from src.lib.logger import Logger
import logging


if __name__ == "__main__":
    args = StartServerCLI().parse_args()
    logger = Logger(args.verbose, args.quiet)
    with InterruptHandler() as handler:
        if args.arquitecture == "select_and_repeat":
            logging.info("[server] Arquitecture select and repeat")
            s = server.ServerSelectAndRepeat(args.host, args.port, args.storage)
            handler.listener(s.close)
            s.listen()
        elif args.arquitecture == "stop_and_wait":
            logging.info("[server] Arquitecture stop and wait")
            s = server.ServerStopAndWait(args.host, args.port, args.storage)  # TO-DO
            handler.listener(s.close)
            s.listen()
        else:
            logging.info(
                "ERROR: Invalid arquitecture. Should be select_and_repeat or stop_and_wait"
            )
