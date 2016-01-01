import sys
from flask import Flask, Markup
from flask.ext.sqlalchemy import SQLAlchemy
from flask_debugtoolbar import DebugToolbarExtension
from markdown import markdown

sys.path.append("../")
try:
    import config.localconfig as localconfig
except:
    print("Error. config/localconfig.py does not exsit")


app = Flask(__name__)

# debug tool is deactive on production
app.debug = localconfig.DEBUG
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


app.config['RECAPTCHA_PUBLIC_KEY'] = localconfig.RECAPTCHA_PUBLIC_KEY
app.config['RECAPTCHA_PRIVATE_KEY'] = localconfig.RECAPTCHA_PRIVATE_KEY

# DB
db = SQLAlchemy(app)


import rabbit_server.views
