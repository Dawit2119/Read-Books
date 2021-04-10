from flask_wtf import FlaskForm
from flask_wtf.file import FileField,FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField,ValidationError,TextAreaField
from wtforms.validators import InputRequired, Length, Email, EqualTo
from models import User
from flask_login import current_user


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[InputRequired(message="Please enter username"), Length(min=2, max=20,message= "Username must be between 5 and 20 characters")])
    email = StringField('Email',
                        validators=[InputRequired(message="Please enter username"), Email(message="Please enter correct email.")])
    password = PasswordField('Password', validators=[InputRequired(message="password is requried")])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[InputRequired(message="confrim password"), EqualTo('password', message="password doesn't match.")])
    submit = SubmitField('Sign Up')
    def validate_username(self,username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("The Username is already taken. choose another one.")
    def validate_email(self,email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("The email is already taken. choose another one.")


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[InputRequired(message="Please enter your email"), Email(message="email is incorrect.")])
    password = PasswordField('Password', validators=[InputRequired(message="password is requried.")])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class AccountUpdateForm(FlaskForm):
    username = StringField('Username',
                           validators=[InputRequired(message="Please enter username"), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[InputRequired(message="Please enter your email"), Email("email is incorrect")])
    profile_picture = FileField('Update Profile Picture',validators=[FileAllowed(['jpg','png'])])
    submit = SubmitField('Update!')
    def validate_username(self,username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError("The Username is already taken. choose another one.")
            
    def validate_email(self,email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError("The email is already taken. choose another one.")
