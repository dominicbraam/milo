from milo.handler.log_handler import Logger


def get_loggers() -> Logger:
    # initialize external module loggers
    Logger("discord").get_logger()
    Logger("openai").get_logger()
    Logger("peewee").get_logger()

    # return local module logger
    return Logger("milo").get_logger()
