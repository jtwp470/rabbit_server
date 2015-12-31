from rabbit_server.models import Config


def get_config(key):
    config = Config.query.filter_by(key=key).first()
    if config:
        return config.value
    else:
        return None
