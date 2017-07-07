from logbook import Logger, FileHandler, StderrHandler
import time


class YPLogger(object):

    def __init__(self, name):
        # 日志文件名
        logfile = 'logs/{0}.log'.format(
            time.strftime("%Y_%m_%d", time.localtime()))

        self.stderr_handler = StderrHandler()
        self.file_handler = FileHandler(logfile, level='INFO', bubble=True)
        self.yp_log = Logger(name)

    def info(self, info_str):
        with self.stderr_handler:
            with self.file_handler:
                self.yp_log.info(info_str)

    def warn(self, warn_str):
        with self.stderr_handler:
            with self.file_handler:
                self.yp_log.warn(warn_str)

    def error(self, error_str):
        with self.stderr_handler:
            with self.file_handler:
                self.yp_log.error(error_str)

    def debug(self, debug_str):
        with self.stderr_handler:
            with self.file_handler:
                self.yp_log.debug(debug_str)
