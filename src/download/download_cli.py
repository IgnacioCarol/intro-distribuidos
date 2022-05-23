import argparse


class DownloadCLI:
    """DOWNLOAD: Transferencia de un archivo del servidor hacia el cliente."""

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog="download",
            usage="download [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [ - d FILEPATH ] [ - n FILENAME ]",
            description="DOWNLOAD: Transferencia de un archivo del servidor hacia el cliente.",
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

        self.parser.add_argument("-d", "--dst", action="store", help="source file path")

        self.parser.add_argument("-n", "--name", action="store", help="file name")

    def parse_args(self):
        return self.parser.parse_args()
