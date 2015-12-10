from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.debug = True
app.config.from_object('rabbit_server.config')

app.jinja_env.globals['apptitle'] = "Rabbit CTF Score Server"
db = SQLAlchemy(app)

import rabbit_server.views
