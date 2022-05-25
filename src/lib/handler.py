import signal


class InterruptHandler(object):
    def __init__(self, signals=(signal.SIGINT, signal.SIGTERM)):
        self.signals = signals
        self.original_handlers = {}
        self.functions = set()

    def __enter__(self):
        self.interrupted = False
        self.released = False

        for sig in self.signals:
            self.original_handlers[sig] = signal.getsignal(sig)
            signal.signal(sig, self._handler)

        return self

    def __exit__(self, type, value, tb):
        self._release()

    def _handler(self, signum, frame):
        self._release()
        self.interrupted = True

    def _release(self):
        if self.released:
            return

        self._handleFinish()
        for sig in self.signals:
            signal.signal(sig, self.original_handlers[sig])

        self.released = True
        # sys.exit()

    def _handleFinish(self):
        # TODO - Integrar con el cierre de los sockets.
        print("Se ejecuta handle finsih del handler")
        for f in self.functions:
            f()

    def listener(self, function):
        self.functions.add(function)
