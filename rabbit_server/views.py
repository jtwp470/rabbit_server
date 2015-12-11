from functools import wraps
from flask import request, redirect, url_for, render_template, session, g, \
    flash, abort
from rabbit_server import app, db
from rabbit_server.models import UserInfo, ProblemTable
from rabbit_server.forms import LoginForm


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('admin', None) is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.before_request
def load_user():
    user_id = session.get('id')
    if user_id is None:
        g.user = None
    else:
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
            if user.id == 1:
                session['admin'] = "admin"
                flash('You are admin!', 'info')
            flash('You were logged in', 'success')
            return redirect(url_for('start_page'))
        else:
            flash('Invalid user or password', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    if session:
        session.clear()
        flash('You were logged out', 'success')
    else:
        flash('Please login', 'warning')
    return redirect(url_for('start_page'))


@app.route('/problem')
@login_required
def top_problem():
    problems = db.session.query(ProblemTable).all()
    return render_template('problem_top.html', problems=problems)


@app.route('/problem/<id>', methods=["GET", "POST"])
@login_required
def view_problem(id):
    problem = db.session.query(ProblemTable).filter(
        ProblemTable.problem_id == id).all()
    # FLAGの提出
    if request.method == "POST":
        flag = request.form["flag"]
        q = db.session.query(ProblemTable).filter(ProblemTable.flag == flag).all()
        print(q)
        if q != []:
            # TODO: INSERT DATABASE
            flash("Congrats!", "success")
        else:
            flash("Invalid your answer", "danger")

    # GET
    if problem:
        return render_template("problem/problem_view.html", problem=problem[0])
    return redirect(url_for('start_page'))


@app.route('/problem/new', methods=["GET", "POST"])
@login_required
@admin_only
# TODO: Admin only
def new_problem():
    """新しい問題を追加する"""
    if request.method == "POST":
        new_problem = ProblemTable(point=int(request.form["point"]),
                                   type=request.form["type"],
                                   title=request.form["title"],
                                   body=request.form["body"],
                                   hint=request.form["hint"],
                                   flag=request.form["flag"])
        db.session.add(new_problem)
        db.session.commit()
        return redirect(url_for('start_page'))
    else:
        return render_template("problem/new.html")


@app.route('/problem/<id>/edit', methods=["GET", "POST"])
@login_required
@admin_only
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
@login_required
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
