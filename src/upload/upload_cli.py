import argparse


class UploadCLI:
    """UPLOAD: Transferencia de un archivo del cliente hacia el servidor."""

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog="upload",
            usage="upload [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [ - s FILEPATH ] [ - n FILENAME ]",
            description="UPLOAD: Transferencia de un archivo del cliente hacia el servidor.",
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

        self.parser.add_argument("-p", "--port", action="store", help="server port")

        self.parser.add_argument("-s", "--src", action="store", help="source file path")

        self.parser.add_argument("-n", "--name", action="store", help="file name")

    def parse_args(self):
        return self.parser.parse_args()
