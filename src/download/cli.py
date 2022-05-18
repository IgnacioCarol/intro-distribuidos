import argparse


class CLI:
    """A simple command-line interface"""

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog='FTP',
            description='File Transfer Protocol'
        )

        self.parser.add_argument(
            'a',
            help='a first argument',
        )

        self.parser.add_argument(
            'b',
            help='a second argument',
        )

        self.parser.add_argument(
            '-v',
            '--verbose',
            action='store_true',
            help='an optional argument'
        )

    def parse_args(self):
        return self.parser.parse_args()
