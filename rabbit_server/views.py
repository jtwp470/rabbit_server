from datetime import datetime
from functools import wraps
from flask import request, redirect, url_for, render_template, session, g, \
    flash, abort
from rabbit_server import app, db
from rabbit_server.models import UserInfo, ProblemTable, ScoreTable
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


def is_admin():
    return "admin" in session


@app.before_request
def load_user():
    user_id = session.get('id')
    if user_id is None:
        g.user = None
    else:
        g.user = UserInfo.query.get(session['id'])


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html.jinja2'), 404


@app.route('/')
def start_page():
    return render_template('index.html.jinja2', is_admin=is_admin())


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('id'):
        # return redirect(url_for('logout'))
        session.clear()

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
    return render_template('login.html.jinja2', form=form)


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
    scores = db.session.query(ScoreTable.problem_id).filter(
        ScoreTable.solved == True).filter(
            ScoreTable.user_id == session.get('id')).all()
    scores = [x[0] for x in scores]
    return render_template('problem_top.html.jinja2',
                           problems=problems, scores=scores)


@app.route('/problem/<id>', methods=["GET", "POST"])
@login_required
def view_problem(id):
    problem = db.session.query(ProblemTable).filter(
        ProblemTable.problem_id == id).first()
    score = db.session.query(ScoreTable).filter(
        ScoreTable.problem_id == id).filter(
            ScoreTable.user_id == session.get('id')).filter(
                ScoreTable.solved == True).first()
    # FLAGの提出
    if request.method == "POST":
        flag = request.form["flag"]
        q = db.session.query(ProblemTable).filter(
            ProblemTable.flag == flag).first()
        if q is not None:
            q = db.session.query(ScoreTable).filter(
                ScoreTable.user_id == int(session['id'])).filter(
                    ScoreTable.problem_id == int(id)).first()
            if q is None:
                flash("Congrats!", "success")
                # INSERT DB
                score = ScoreTable(user_id=int(session['id']),
                                   problem_id=int(id),
                                   solved=True,
                                   solved_time=datetime.now())
                db.session.add(score)
                db.session.commit()
                # 得点を更新
                update_user = UserInfo.query.filter(UserInfo.id == int(session['id'])).first()
                update_user.score += problem.point
                db.session.add(update_user)
                db.session.commit()
            else:
                flash("Error: CANNOT re-submit flag that solved", "danger")
        else:
            # TODO: Record invalid answer to db & views admin only.
            flash("Invalid your answer", "danger")

    # For GET request
    if problem:
        return render_template("problem/problem_view.html.jinja2",
                               problem=problem, score=score, is_admin=is_admin())
    return redirect(url_for('start_page'))


@app.route('/problem/new', methods=["GET", "POST"])
@login_required
@admin_only
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
        return redirect(url_for('view_problem', id=new_problem.problem_id))
    else:
        return render_template("problem/new.html.jinja2")


@app.route('/problem/<id>/edit', methods=["GET", "POST"])
@login_required
@admin_only
def edit_problem(id):
    """既存の問題を編集する"""
    problem = db.session.query(ProblemTable).filter(
        ProblemTable.problem_id == id).first()
    if request.method == "POST":
        problem.point = int(request.form["point"])
        problem.type = request.form["type"]
        problem.body = request.form["body"]
        problem.hint = request.form["hint"]
        problem.flag = request.form["flag"]

        # db.session.update(problem, synchronize_session=False)
        db.session.commit()
        flash('Success update problem', 'success')
        return redirect(url_for('view_problem', id=problem.problem_id))
    elif problem:
        return render_template("problem/edit.html.jinja2", problem=problem)
    else:
        return abort(404)


@app.route('/ranking')
def view_ranking():
    users = db.session.query(UserInfo).order_by(UserInfo.score.desc()).all()
    return render_template('ranking.html.jinja2', users=users)


@app.route('/rule')
def view_rule():
    return render_template('rule.html.jinja2')


@app.route('/notice')
def view_notice():
    return render_template('notice.html.jinja2')


@app.route('/user/<id>')
@login_required
def view_user(id):
    user = db.session.query(UserInfo).filter(UserInfo.id == id).first()
    # SELECT * FROM score JOIN problem WHERE user_id = id
    solved = db.session.query(ScoreTable, ProblemTable).join(ProblemTable).filter(
        ScoreTable.user_id == id).group_by(ProblemTable.problem_id).all()
    if user:
        return render_template('user_info.html.jinja2',
                               user=user, solved=solved, your_id=session['id'])
    else:
        abort(404)


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == 'POST' and session.get('id') is None:
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
        return render_template('register.html.jinja2')
