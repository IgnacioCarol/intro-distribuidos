from threading import Timer


class RepeatingTimer(object):
    def __init__(self, interval, func, *args, **kwargs):
        self.interval = interval
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.timer = None
        self.nack = 0

    def callback(self):
        self.func(*self.args, **self.kwargs)
        self.start()

    def cancel(self):
        self.timer.cancel()

    def start(self):
        self.nack += 1
        if self.nack > 20:
            self.cancel()
            return
        self.timer = Timer(self.interval, self.callback)
        self.timer.start()
