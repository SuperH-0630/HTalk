from configure import configure

import os
import logging

env_dict = os.environ
htalk_conf = env_dict.get("HTALK_CONF")
if htalk_conf is None:
    logging.info("Configure file ./etc/conf.json")
    configure("./etc/conf.json")
else:
    logging.info(f"Configure file {htalk_conf}")
    configure(htalk_conf)


from app import HTalkFlask
app = HTalkFlask(__name__)


@app.shell_context_processor
def make_shell_context():
    from app.db import (db, create_all,
                        create_faker_user,
                        create_faker_comment,
                        create_faker_archive,
                        create_fake_archive_comment,
                        create_fake_follow)
    return {
        "app": app,
        "db": db,
        "create_all": create_all,
        "create_faker_user": create_faker_user,
        "create_faker_comment": create_faker_comment,
        "create_faker_archive": create_faker_archive,
        "create_fake_archive_comment": create_fake_archive_comment,
        "create_fake_follow": create_fake_follow,
    }
