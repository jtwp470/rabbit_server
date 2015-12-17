from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask_debugtoolbar import DebugToolbarExtension


app = Flask(__name__)

# debug tool is deactive on production
app.debug = True
app.config['SECRET_KEY'] = "SECRETSECRETSECRET"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
toolbar = DebugToolbarExtension(app)


# confs
app.config.from_object('rabbit_server.config')
app.jinja_env.globals['apptitle'] = "Rabbit CTF Score Server"


def datetimeformat(value, format='%Y/%m/%d %H:%M'):
    return value.strftime(format)

app.jinja_env.filters['datetimeformat'] = datetimeformat

# DB
db = SQLAlchemy(app)


import rabbit_server.views
