from flask import Flask, Markup
from flask.ext.sqlalchemy import SQLAlchemy
from flask_debugtoolbar import DebugToolbarExtension
from markdown import markdown


app = Flask(__name__)

# debug tool is deactive on production
app.debug = True
app.config['SECRET_KEY'] = "SECRETSECRETSECRET"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
toolbar = DebugToolbarExtension(app)


# confs
app.config.from_object('rabbit_server.config')
app.jinja_env.globals['apptitle'] = "Rabbit CTF Score Server"


@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y/%m/%d %H:%M'):
    return value.strftime(format)


@app.template_filter('markdown')
def markdown_filter(content):
    return Markup(markdown(content, extensions=['gfm']))


# DB
db = SQLAlchemy(app)


import rabbit_server.views
