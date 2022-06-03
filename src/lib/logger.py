import logging


class Logger:
    def __init__(self, verbose, quiet):

        if quiet:
            logging.basicConfig(level=logging.ERROR)
        elif verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
