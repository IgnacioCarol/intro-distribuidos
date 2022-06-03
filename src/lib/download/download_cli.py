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
            "-v",
            "--verbose",
            action="store_false",
            help="verbose increase output verbosity",
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
            "-d", "--dst", action="store", help="source file path", required=True
        )

        self.parser.add_argument(
            "-n", "--name", action="store", help="file name", required=True
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
