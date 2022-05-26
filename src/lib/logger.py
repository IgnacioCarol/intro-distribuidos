import logging


class Logger:
    def __init__(self, verbose, quiet):

        if verbose:
            logging.basicConfig(level=logging.DEBUG)
        elif quiet:
            logging.basicConfig(level=logging.WARNING)
        else:
            logging.basicConfig(level=logging.INFO)
