from milo.loggers import get_loggers

app_logger = get_loggers()


def default():
    return "This is the default response."
