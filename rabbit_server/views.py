from functools import wraps
from flask import request, redirect, url_for, render_template, session, g
from rabbit_server import app, db
from rabbit_server.models import UserInfo
from rabbit_server.forms import LoginForm


def login_required(f):
    @wraps(f)
    def decorated_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated_view


@app.before_request
def load_user():
    user_id = session.get('id')
    if user_id is None:
        g.user = None
    else:
        g.user = UserInfo.query.get(session['id'])


@app.route('/')
def start_page():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user, authenticated = UserInfo.authenticate(db.session.query,
                                                    form.name.data,
                                                    form.password.data)
        if authenticated:
            session['id'] = user.id
            session['name'] = user.name
            # flash('<div class="alert alert-success" role="alert">You were logged in</div>')
            return redirect(url_for('index'))
        # else:
        # flash('<div class="alert alert-danger" role="alert">Invalid user or password</div>')
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    if session:
        session.clear()
    # flash('<div class="alert alert-success" role="alert">You were logged out</div>')
    return redirect('/')
