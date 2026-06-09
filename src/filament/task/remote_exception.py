class FilamentRemoteException(Exception):
    def __init__(self, exc_type, message, traceback=None):
        self.exc_type = exc_type
        self.message = message
        self.traceback = traceback

    def __str__(self):
        result = f'{self.exc_type.__name__}: {self.message}'
        if self.traceback:
            result += f'\n{self.traceback}'
        return result

    def __repr__(self):
        return f'{self.exc_type.__name__}: {self.message}'
