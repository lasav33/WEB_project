from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import SubmitField
from wtforms.validators import DataRequired


class QuestForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField("Вопрос")
    submit = SubmitField('Применить')


class CommsForm(FlaskForm):
    content = TextAreaField('')
    submit = SubmitField('Отправить')
