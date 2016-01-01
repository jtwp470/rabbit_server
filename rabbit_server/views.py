from urllib.parse import urlparse, urljoin
from datetime import datetime
from functools import wraps
from flask import request, redirect, url_for, render_template, session, g, \
    flash, abort, jsonify
from rabbit_server import app, db
from rabbit_server.models import UserInfo, ProblemTable, ScoreTable, \
    WrongAnswerTable, NoticeTable, Config
from rabbit_server.forms import LoginForm, RegisterForm
from rabbit_server.util import get_config


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('admin', None) is None:
            return redirect(url_for('login', next=request.path))
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
    return render_template('404.html'), 404


@app.route('/')
def start_page():
    text = get_config('root_text')
    if text is None:
        text = ""
    return render_template('index.html', text=text, is_admin=is_admin())


@app.route('/edit', methods=['GET', 'POST'])
@admin_only
def edit_start_page():
    config = db.session.query(Config).filter(
        Config.key == "root_text").first()
    if request.method == "POST":
        if config is None:
            config = Config(key="root_text",
                            value=request.form['text'])
            db.session.add(config)
        else:
            config.value = request.form['text']
        db.session.commit()
        return redirect(url_for('start_page'))
    else:
        return render_template('index.html',
                               edit=True, is_admin=is_admin())


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


def get_redirect_target():
    for target in request.values.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target


def redirect_back(endpoint, **values):
    target = request.form['next']
    if not target or not is_safe_url(target):
        target = url_for(endpoint, **values)
    return redirect(target)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('id'):
        # return redirect(url_for('logout'))
        session.clear()
    next = get_redirect_target()
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
            return redirect_back('start_page')
        else:
            flash('Invalid user or password', 'danger')
    return render_template('login.html', form=form, next=next)


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
    problems = db.session.query(ProblemTable)
    if is_admin() is False:
        problems = problems.filter(ProblemTable.is_public == True)
    problems = problems.all()
    scores = db.session.query(ScoreTable.problem_id).filter(
        ScoreTable.solved == True).filter(
            ScoreTable.user_id == session.get('id')).all()
    scores = [x[0] for x in scores]
    return render_template('problem_top.html',
                           problems=problems, scores=scores,
                           is_admin=is_admin())


@app.route('/problem/<id>', methods=["GET", "POST"])
@login_required
def view_problem(id):
    session_id = session.get('id', -1)
    problem = db.session.query(ProblemTable).filter(
        ProblemTable.problem_id == id)
    if is_admin() is False:
        problem = problem.filter(ProblemTable.is_public == True)
    problem = problem.first()
    score = db.session.query(ScoreTable).filter(
        ScoreTable.problem_id == id).filter(
            ScoreTable.user_id == session_id).filter(
                ScoreTable.solved == True).first()
    # FLAGの提出
    if request.method == "POST":
        flag = request.form["flag"]
        q = db.session.query(ProblemTable).filter(
            ProblemTable.flag == flag).first()
        if q is not None:
            q = db.session.query(ScoreTable).filter(
                ScoreTable.user_id == session_id).filter(
                    ScoreTable.problem_id == id).first()
            if q is None:
                flash("Congrats!", "success")
                # INSERT DB
                score = ScoreTable(user_id=session_id,
                                   problem_id=int(id),
                                   solved=True,
                                   solved_time=datetime.now())
                db.session.add(score)
                db.session.commit()
                # 得点を更新
                update_user = UserInfo.query.filter(
                    UserInfo.id == session_id).first()
                update_user.score += problem.point
                db.session.add(update_user)
                db.session.commit()
            else:
                flash("Error: CANNOT re-submit flag that solved", "danger")
        else:
            # Record invalid answer
            wrong_answer = WrongAnswerTable(
                user_id=session_id,
                problem_id=id,
                wa=flag,
                date=datetime.now())
            db.session.add(wrong_answer)
            db.session.commit()
            flash("Invalid your answer", "danger")

    # For GET request
    if problem:
        return render_template("problem/problem_view.html",
                               problem=problem, score=score,
                               is_admin=is_admin())
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
                                   flag=request.form["flag"],
                                   is_public=(request.form.get
                                              ("is_public") is not None))
        db.session.add(new_problem)
        db.session.commit()
        return redirect(url_for('view_problem', id=new_problem.problem_id))
    else:
        return render_template("problem/new.html")


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
        problem.is_public = (request.form.get("is_public") is not None)

        # db.session.update(problem, synchronize_session=False)
        db.session.commit()
        flash('Success update problem', 'success')
        return redirect(url_for('view_problem', id=problem.problem_id))
    elif problem:
        return render_template("problem/edit.html",
                               problem=problem,
                               is_admin=is_admin())
    else:
        return abort(404)


@app.route('/ranking')
def view_ranking():
    users = db.session.query(UserInfo).order_by(UserInfo.score.desc()).all()
    return render_template('ranking.html',
                           users=users, is_admin=is_admin())


@app.route('/rule')
def view_rule():
    text = get_config('rule_text')
    if text is None:
        text = ""
    return render_template('rule.html',
                           text=text, is_admin=is_admin())


@app.route('/role/edit', methods=["GET", "POST"])
def edit_rule_page():
    config = db.session.query(Config).filter(
        Config.key == "rule_text").first()
    if request.method == "POST":
        if config is None:
            config = Config(key="rule_text",
                            value=request.form['text'])
            db.session.add(config)
        else:
            config.value = request.form['text']
        db.session.commit()
        return redirect(url_for('view_rule'))
    else:
        return render_template('rule.html',
                               edit=True, is_admin=is_admin())


@app.route('/notice')
def view_notice():
    notices = db.session.query(NoticeTable).order_by(
        NoticeTable.date.desc()).all()
    last_id = 1
    if len(notices) >= 1:
        last_id = notices[-1].id + 1

    return render_template('notice.html',
                           notices=notices,
                           last_id=last_id,
                           is_admin=is_admin())


@app.route('/notice/<id>')
def view_notice_id(id):
    notice = db.session.query(NoticeTable).get(id)
    if notice is None:
        notice = {}
    else:
        notice = notice.serialize()
    return jsonify(notice)


@app.route('/notice/<id>/edit', methods=["GET", "POST"])
@admin_only
def edit_notice(id):
    notice = db.session.query(NoticeTable).filter(NoticeTable.id == id).first()
    if request.method == 'POST':
        if notice:  # UPDATE notice
            notice.title = request.form["title"]
            notice.body = request.form["body"]
            notice.date = datetime.now()
        else:
            notice = NoticeTable(
                title=request.form["title"],
                body=request.form["body"],
                date=datetime.now())
            db.session.add(notice)
        db.session.commit()
        return redirect(url_for('view_notice'))
    else:
        return render_template('new_notice.html', id=id)


@app.route('/log')
@admin_only
def view_log():
    wrong_answers = db.session.query(
        WrongAnswerTable, UserInfo, ProblemTable).join(UserInfo).join(
            ProblemTable).all()
    return render_template('log.html',
                           wrong_answers=wrong_answers, is_admin=is_admin())


@app.route('/user/<id>')
@login_required
def view_user(id):
    user = db.session.query(UserInfo).filter(UserInfo.id == id).first()
    # SELECT * FROM score JOIN problem WHERE user_id = id
    solved = db.session.query(ScoreTable, ProblemTable).join(
        ProblemTable).filter(ScoreTable.user_id == id).group_by(
            ProblemTable.problem_id).all()
    if user:
        return render_template('user_info.html',
                               user=user, solved=solved,
                               your_id=session['id'],
                               is_admin=is_admin())
    else:
        abort(404)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit() and session.get('id') is None:
        user = UserInfo()
        user_exist = UserInfo.query.filter_by(name=form.username.data).first()
        if user_exist:
            form.username.errors.append(
                'Username already taken. Please change')
            return render_template('register.html', form=form)
        else:
            user.name = form.username.data
            user.email = form.email.data
            user.password = form.password.data
            user.score = 0
            db.session.add(user)
            db.session.commit()
            # ログインしたことにする
            session['id'] = user.id
            session['name'] = user.name
            return redirect(url_for('start_page'))
    else: # GET
        return render_template('register.html', form=form)
