from src.start_server.start_server_cli import StartServerCLI
from src.start_server.start_server import Server
from src.lib.handler import InterruptHandler


if __name__ == "__main__":
    args = StartServerCLI().parse_args()
    with InterruptHandler() as handler:
        s = Server(args.host, args.port, args.storage)
        handler.listener(s.close)
        s.listen()
