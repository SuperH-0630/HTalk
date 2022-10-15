from configure import configure

import os
import logging

env_dict = os.environ
hblog_conf = env_dict.get("hblog_conf")
if hblog_conf is None:
    logging.info("Configure file ./etc/conf.json")
    configure("./etc/conf.json")
else:
    logging.info(f"Configure file {hblog_conf}")
    configure(hblog_conf)


from app import HTalkFlask
app = HTalkFlask(__name__)


@app.shell_context_processor
def make_shell_context():
    from app.db import db
    return {
        "app": app,
        "db": db,
    }
