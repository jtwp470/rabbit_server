from functools import wraps
from flask import request, redirect, url_for, render_template, session, g, \
    flash, abort
from rabbit_server import app, db
from rabbit_server.models import UserInfo, ProblemTable
from rabbit_server.forms import LoginForm

is_admin = False


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
        if user_id == 1:
            is_admin = True
            print("This is admin")
            g.user = UserInfo.query.get(session['id'])


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


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
            flash('You were logged in', 'success')
            return redirect(url_for('start_page'))
        else:
            flash('Invalid user or password', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    if session:
        session.clear()
        flash('You were logged out', 'success')
    else:
        flash('Please login', 'warning')
    return redirect(url_for('start_page'))


@app.route('/admin/add', methods=["GET", "POST"])
def add_admin():
    admin = db.session.query(UserInfo).filter(UserInfo.id == 1).all()
    if admin == []:
        if request.method == 'POST':
            # Adminを作成する
            if request.form['password'] == request.form['re_password']:

                admin = UserInfo(name=request.form['name'],
                                 mail=request.form['mail'],
                                 password=request.form['password'],
                                 score=0)
                db.session.add(admin)
                db.session.commit()
                # ログインしたことにする
                session['id'] = admin.id
                session['name'] = admin.name
                return redirect(url_for('start_page'))
            else:
                flash('Password is not match! Please retype password',
                      'danger')
                return redirect(url_for('add_admin'))
        else:
            return render_template('admin/add.html')
    return redirect(url_for('start_page'))


@app.route('/problem')
def top_problem():
    return render_template('problem_top.html')


@app.route('/problem/<id>')
def view_problem(id):
    problem = db.session.query(ProblemTable).filter(ProblemTable.problem_id == id).all()
    if problem:
        return render_template("problem/problem_view.html", problem=problem[0])
    return redirect(url_for('start_page'))


@app.route('/problem/new', methods=["GET", "POST"])
# TODO: Admin only
def new_problem():
    """新しい問題を追加する"""
    if request.method == "POST":
        new_problem = ProblemTable(point=int(request.form["point"]),
                                   type=request.form["type"],
                                   title=request.form["title"],
                                   body=request.form["body"],
                                   hint=request.form["hint"])
        db.session.add(new_problem)
        db.session.commit()
        return redirect(url_for('start_page'))
    else:
        return render_template("problem/new.html")


@app.route('/problem/<id>/edit', methods=["GET", "POST"])
# TODO: Admin only
def edit_problem(id):
    """既存の問題を編集する"""
    pass


@app.route('/ranking')
def view_ranking():
    return render_template('ranking.html')


@app.route('/rule')
def view_rule():
    return render_template('rule.html')


@app.route('/notice')
def view_notice():
    return render_template('notice.html')


@app.route('/user/<id>')
def view_user(id):
    user = db.session.query(UserInfo).filter(UserInfo.id == id).all()
    if user:
        return render_template('user_info.html', user=user[0])
    else:
        abort(404)


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        if request.form['password'] == request.form['re_password']:
            user = UserInfo(name=request.form['name'],
                            mail=request.form['mail'],
                            password=request.form['password'],
                            score=0)
            db.session.add(user)
            db.session.commit()
            # ログインしたことにする
            session['id'] = user.id
            session['name'] = user.name
            return redirect(url_for('start_page'))
        else:
            flash('Password is not match! Please retype password',
                  'danger')
            return redirect(url_for('register'))
    else: # GET
        return render_template('register.html')
