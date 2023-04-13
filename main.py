import flask
from flask import Flask, abort
from data import db_session
from data.users import User
from data.questions import Questions
from data.comments import Comments
from forms.user import RegisterForm, LoginForm
from forms.forum import QuestForm, CommsForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

db_session.global_init("db/blogs.db")

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/quest', methods=['GET', 'POST'])
@login_required
def add_quest():
    form = QuestForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        quest = Questions()
        quest.title = form.title.data
        quest.content = form.content.data
        current_user.questions.append(quest)
        db_sess.merge(current_user)
        db_sess.commit()
        return flask.redirect('/')
    return flask.render_template('quest.html', title='Добавление вопроса',
                                 form=form)


@app.route('/quest/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_quest(id):
    form = QuestForm()
    if flask.request.method == "GET":
        db_sess = db_session.create_session()
        quest = db_sess.query(Questions).filter(Questions.id == id,
                                                Questions.user == current_user
                                                ).first()
        if quest:
            form.title.data = quest.title
            form.content.data = quest.content
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        quest = db_sess.query(Questions).filter(Questions.id == id,
                                                Questions.user == current_user
                                                ).first()
        if quest:
            quest.title = form.title.data
            quest.content = form.content.data
            db_sess.commit()
            return flask.redirect('/')
        else:
            abort(404)
    return flask.render_template('quest.html',
                                 title='Редактирование вопроса',
                                 form=form
                                 )


@app.route('/quest_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def quest_delete(id):
    db_sess = db_session.create_session()
    quest = db_sess.query(Questions).filter(Questions.id == id,
                                            Questions.user == current_user
                                            ).first()
    if quest:
        db_sess.delete(quest)
        db_sess.commit()
    else:
        abort(404)
    return flask.redirect('/')


@app.route("/")
def index():
    db_sess = db_session.create_session()
    quest = db_sess.query(Questions).order_by(Questions.col_likes.desc()).all()
    return flask.render_template("index.html", news=quest)


@app.route("/comments/<int:id>", methods=['GET', 'POST'])
def comments(id):
    form = CommsForm()
    db_sess = db_session.create_session()
    coms = db_sess.query(Comments).filter(Comments.questions_id == id)
    quar = db_sess.query(Questions).filter(Questions.id == id).first()
    if form.validate_on_submit():
        coms = Comments()
        coms.content = form.content.data
        current_user.comments.append(coms)
        coms.questions_id = id
        db_sess.merge(current_user)
        db_sess.commit()
        return flask.redirect(f'/comments/{id}')
    return flask.render_template('coms.html', coms=coms,
                                 form=form, qur_name=quar.title, qur_content=quar.content)


@app.route('/comments_change/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_comments(id):
    form = CommsForm()
    db_sess = db_session.create_session()
    if flask.request.method == "GET":
        db_sess = db_session.create_session()
        coms = db_sess.query(Comments).filter(Comments.id == id,
                                              Comments.user == current_user
                                              ).first()
        if coms:
            form.content.data = coms.content
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        coms = db_sess.query(Comments).filter(Comments.id == id,
                                              Comments.user == current_user
                                              ).first()
        if coms:
            coms.content = form.content.data
            db_sess.commit()
            return flask.redirect(f'/comments/{coms.questions_id}')
        else:
            abort(404)
    return flask.render_template('coms.html',
                                 form=form
                                 )


@app.route('/comments_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def comments_delete(id):
    db_sess = db_session.create_session()
    coms = db_sess.query(Comments).filter(Comments.id == id,
                                          Comments.user == current_user
                                          ).first()
    quest_id = coms.questions_id
    if coms:
        db_sess.delete(coms)
        db_sess.commit()
    else:
        abort(404)
    return flask.redirect(f'/comments/{quest_id}')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return flask.redirect("/")


@app.route('/like/<id_user>/<id_com>')
@login_required
def like(id_user, id_com):
    db_sess = db_session.create_session()
    quest = db_sess.query(Questions).filter(Questions.id == id_com).first()
    if quest:
        if str(id_user) not in quest.likes:
            quest.likes = quest.likes + str(id_user) + ' '
            quest.col_likes = len(quest.likes.split())
            db_sess.add(quest)
            db_sess.commit()
    return flask.redirect("/")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return flask.redirect("/")
        return flask.render_template('login.html',
                                     message="Неправильный логин или пароль",
                                     form=form)
    return flask.render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return flask.render_template('register.html', title='Регистрация',
                                         form=form,
                                         message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return flask.render_template('register.html', title='Регистрация',
                                         form=form,
                                         message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return flask.redirect('/login')
    return flask.render_template('register.html', title='Регистрация', form=form)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
