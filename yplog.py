import logbook
import time
import os

logbook.set_datetime_format("local")


class YPLogger(object):

    def __init__(self, name, package):
        root_path = os.path.dirname(__file__)
        log_dir = '{0}\\{1}\\logs\\'.format(
            root_path, package)
        if not os.path.isdir(log_dir):
            os.mkdir(log_dir)
        # 日志文件名
        logfile = '{0}{1}.log'.format(
            log_dir,
            time.strftime("%Y_%m_%d", time.localtime()))

        self.stderr_handler = logbook.StderrHandler()
        self.file_handler = logbook.FileHandler(logfile, level='INFO', bubble=True)
        self.yp_log = logbook.Logger(name)

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
