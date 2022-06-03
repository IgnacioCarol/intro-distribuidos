import argparse


class StartServerCLI:
    """Interfaz del servidor"""

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog="start-server",
            usage="start-server [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [- s DIRPATH ]",
            description="Interfaz del servidor",
        )

        self.parser.add_argument(
            "-v", "--verbose", action="store_false", help="verbose increase output verbosity"
        )

        self.parser.add_argument(
            "-q", "--quiet", action="store_true", help="quiet decrease output verbosity"
        )

        self.parser.add_argument(
            "-H", "--host", action="store", help="server IP address", required=True
        )

        self.parser.add_argument(
            "-p", "--port", action="store", help="server port", type=int, required=True
        )

        self.parser.add_argument(
            "-s", "--storage", action="store", help="storage dir path", required=True
        )

        self.parser.add_argument(
            "-a",
            "--arquitecture",
            action="store",
            help="arquitecture: select_and_repeat or stop_and_wait",
            default="select_and_repeat",
        )

    def parse_args(self):
        return self.parser.parse_args()
