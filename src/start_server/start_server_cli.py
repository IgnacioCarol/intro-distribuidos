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
            "-v", "--verbose", action="store", help="verbose increase output verbosity"
        )

        self.parser.add_argument(
            "-q", "--quit", action="store", help="quiet decrease output verbosity"
        )

        self.parser.add_argument(
            "-H", "--host", action="store", help="server IP address"
        )

        self.parser.add_argument(
            "-p", "--port", action="store", help="server port", type=int
        )

        self.parser.add_argument(
            "-s", "--storage", action="store", help="storage dir path"
        )

    def parse_args(self):
        return self.parser.parse_args()
