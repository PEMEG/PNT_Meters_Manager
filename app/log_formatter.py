import logging
import os

log = logging.getLogger()


class LogFormatter(logging.Formatter):

    bright_red = "\x1b[91;20m"
    blue = "\x1b[94;20m"
    grey = "\x1b[90;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[41;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s | %(levelname)-8s | %(message)s"
    date_format = f"{grey}%(asctime)s {reset}"

    FORMATS = {
        logging.DEBUG: f"{date_format}|"
                       f"{blue} %(levelname)-8s {reset}|"
                       f" %(message)s",
        logging.INFO: f"{date_format}|"
                      f"{grey} %(levelname)-8s {reset}|"
                      f" %(message)s",
        logging.WARNING: f"{date_format}|"
                         f"{yellow} %(levelname)-8s {reset}|"
                         f" %(message)s",
        logging.ERROR: f"{date_format}|"
                       f"{red} %(levelname)-8s {reset}|"
                       f" %(message)s",
        logging.CRITICAL: f"{date_format}|"
                          f"{bold_red} %(levelname)-8s {reset}|"
                          f" {bright_red}%(message)s{reset}"
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, "%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

    @staticmethod
    def get_level() -> int:
        level = os.getenv('DEBUG', '0')
        if level == "1":
            return logging.DEBUG
        return logging.INFO


def log_setup() -> None:
    formatter = "%(asctime)s | %(levelname)-8s | %(message)s"
    _log = logging.getLogger()
    _log.setLevel(LogFormatter.get_level())
    ch = logging.StreamHandler()
    ch.setLevel(LogFormatter.get_level())
    ch.setFormatter(LogFormatter())
    _log.addHandler(ch)
    try:
        fh = logging.FileHandler('logs/app.log')
        fh.setFormatter(logging.Formatter(formatter))
        fh.setLevel(logging.WARNING)
        _log.addHandler(fh)
    except Exception as error:
        _log.exception(error)


def level_test() -> None:
    log.debug("debug message")
    log.info("info message")
    log.warning("warn message")
    log.error("error message")
    log.critical("critical message")
