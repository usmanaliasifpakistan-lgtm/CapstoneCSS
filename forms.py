from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField

##WTForm
class NewPostForm(FlaskForm):
    title = StringField('Title', validators = [DataRequired()])
    body = CKEditorField('Blog Content', validators=[DataRequired()])
    subtitle = StringField('Subtitle', validators = [DataRequired()])
    img_url = StringField('Image URL', validators = [DataRequired()])
    submit = SubmitField('Submit')

#Register Form
class RegisterForm(FlaskForm):
    name = StringField('Name: ', validators = [DataRequired()])
    email = StringField('Email: ', validators = [DataRequired()])
    password = PasswordField(label="Password: ", validators = [DataRequired()])
    submit = SubmitField('Submit')


#Login Form
class LoginForm(FlaskForm):
    email = StringField('Email: ', validators=[DataRequired()])
    password = PasswordField(label="Password: ", validators=[DataRequired()])
    submit = SubmitField('Submit')

class CommentForm(FlaskForm):
    comment = CKEditorField('Comment', validators=[DataRequired()])
    submit = SubmitField('Submit')