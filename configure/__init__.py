import json
import logging
import os
from typing import Dict


conf: Dict[str, any] = {
    "DEBUG_PROFILE": False,
    "LOG_STDERR": True,
    "LOG_LEVEL": "info",
    "LOG_HOME": "",
    "LOG_FORMAT": "[%(levelname)s]:%(name)s:%(asctime)s "
                  "(%(filename)s:%(lineno)d %(funcName)s) "
                  "%(process)d %(thread)d "
                  "%(message)s",

    "SECRET_KEY": "11111111",
    "SQLALCHEMY_DATABASE_URI": "mysql+pymysql://root:12345678@localhost:3306/htalk",
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
}


def configure(conf_file: str, encoding="utf-8"):
    """ 运行配置程序, 该函数需要在其他模块被执行前调用 """
    with open(conf_file, mode="r", encoding=encoding) as f:
        json_str = f.read()
        conf.update(json.loads(json_str))

    if type(conf["LOG_LEVEL"]) is str:
        conf["LOG_LEVEL"] = {"debug": logging.DEBUG,
                             "info": logging.INFO,
                             "warning": logging.WARNING,
                             "error": logging.ERROR}.get(conf["LOG_LEVEL"])
    if len(conf["LOG_HOME"]) > 0:
        os.makedirs(conf["LOG_HOME"], exist_ok=True)