import logging


class Logger:

    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)

        dt_fmt = "%Y-%m-%d %H:%M:%S"
        logFormatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(funcName)s:%(lineno)d - %(message)s",
            dt_fmt,
        )

        fileHandler = logging.FileHandler(f"logs/{logger_name}.log")
        fileHandler.setFormatter(logFormatter)
        self.logger.addHandler(fileHandler)

    def get_logger(self):
        return self.logger
