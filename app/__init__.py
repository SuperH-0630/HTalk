from flask import Flask
from flask.logging import default_handler
import logging
import logging.handlers
import os
import sys

from .db import db
from .moment import moment
from .mail import mail
from .migrate import migrate

from configure import conf


if conf["DEBUG_PROFILE"]:
    from werkzeug.middleware.profiler import ProfilerMiddleware


class HTalkFlask(Flask):
    def __init__(self, name):
        super(HTalkFlask, self).__init__(name)
        self.update_configure()
        self.profile_setting()
        self.logging_setting()

        db.init_app(self)
        moment.init_app(self)
        mail.init_app(self)
        migrate.init_app(self)

    def profile_setting(self):
        if conf["DEBUG_PROFILE"]:
            self.wsgi_app = ProfilerMiddleware(self.wsgi_app, sort_by=("cumtime",))

    def logging_setting(self):
        self.logger.removeHandler(default_handler)
        self.logger.setLevel(conf["LOG_LEVEL"])
        self.logger.propagate = False  # 不传递给更高级别的处理器处理日志

        if len(conf["LOG_HOME"]) > 0:
            handle = logging.handlers.TimedRotatingFileHandler(
                os.path.join(conf["LOG_HOME"], f"flask.log"), backupCount=10)
            handle.setFormatter(logging.Formatter(conf["LOG_FORMAT"]))
            self.logger.addHandler(handle)

        if conf["LOG_STDERR"]:
            handle = logging.StreamHandler(sys.stderr)
            handle.setFormatter(logging.Formatter(conf["LOG_FORMAT"]))
            self.logger.addHandler(handle)

    def update_configure(self):
        """ 更新配置 """
        self.config.update(conf)
