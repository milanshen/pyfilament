import logging


class UnixTimeFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        t = round(record.created, 1)
        return f'{t:.1f}'


def setup_logging():
    formatter = UnixTimeFormatter(fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)
    rootLogger.handlers = [handler]  # Replace any existing handlers


setup_logging()
