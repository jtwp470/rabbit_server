from rabbit_server.models import Config
from flask import flash


def get_config(key):
    config = Config.query.filter_by(key=key).first()
    if config:
        return config.value
    else:
        return None
