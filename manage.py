from flask.ext.script import Manager
from rabbit_server import app, db
from config import localconfig


manager = Manager(app)


@manager.command
def init_db():
    db.create_all()


if __name__ == "__main__":
    manager.run()
