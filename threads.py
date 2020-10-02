from threading import Thread


class RunInThread:
    """
    decorator to run the method in a thread
    """
    def __init__(self, f):
        self.f = f

    def __call__(self, *args, **kwargs):
        Thread(target=lambda: self.f(*args, **kwargs)).start()
