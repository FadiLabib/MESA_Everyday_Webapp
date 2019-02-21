"""
This file contains all the forms used throughout the application
The application uses the flask_wtf library for creating forms
Each class only needs to describe what fields are in the form and how the fields should be validated

Modified from CoreyMSchafer's Flask Tutorial
https://github.com/CoreyMSchafer/code_snippets/blob/master/Python/Flask_Blog/06-Login-Auth/flaskblog/routes.py
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, DateField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Regexp, Optional
from MESAeveryday.models import User, School, Badge, Stamp, Reset_Date
from flask_login import current_user
from MESAeveryday import bcrypt
from datetime import datetime

def positive(form, field):
        if field.data != None and field.data < 1:
            raise ValidationError('Number must be positive.')

class RegistrationForm(FlaskForm):
    firstname = StringField('Firstname', validators=[DataRequired()])
    lastname = StringField('Lastname', validators=[DataRequired()])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    school = SelectField('School', coerce=int, choices=School.get_all_schools_names())
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, message="your password must be at least %(min)d characters")
                                 , Regexp("^(?=.*[0-9])(?=.*[!@#\$%\^&\*])",
                                          message="The string must contain at least 1 numeric digit and 1 symbol")])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        if User.get_user_by_email(email.data):
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class RequestResetForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.validate_email(email)
        if user == False:
            raise ValidationError('There is no account with that email. You must regester first.')

class RequestResetUserForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Request User Reset')

    def validate_email(self, email):
        user = User.validate_email(email)
        if user == False:
            raise ValidationError('There is no account with that email. You must regester first.')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password',  validators=[DataRequired(), Length(min=8, message="your password must be at least %(min)d characters")
                                 , Regexp("^(?=.*[0-9])(?=.*[!@#\$%\^&\*])",
                                          message="The string must contain at least 1 numeric digit and 1 symbol")])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class UpdateEmailForm(FlaskForm):

    email = StringField('Email', validators=[Email()])
	
    submit = SubmitField('Update Email')
    
    def validate_email(self, email):
        if User.get_user_by_email(email.data):
            raise ValidationError('That email is taken. Please choose a different one.')

class UpdateNameForm(FlaskForm):

    firstname = StringField('Firstname')
    lastname = StringField('Lastname')

    submit = SubmitField('Update Name')

class UpdateSchoolForm(FlaskForm):

    school = SelectField('School', coerce=int, choices=School.get_all_schools_names())

    submit = SubmitField('Update School')

class UpdatePasswordForm(FlaskForm):
    old_password = PasswordField('Password')
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8,
                                                                            message="your password must be at least %(min)d characters")
        , Regexp("^(?=.*[0-9])(?=.*[!@#\$%\^&\*])",
                 message="The string must contain at least 1 numeric digit and 1 symbol")])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Update Password')
    
    def validate_old_password(self, old_password):

        if not bcrypt.check_password_hash(current_user.password, old_password.data):
            raise ValidationError('Old password is not correct.')

class EarnStampsForm(FlaskForm):
    stamps = SelectField('Stamp', coerce=int)
    time_finished = DateField('time finished', format='%m/%d/%Y', validators=[DataRequired()])
    submit = SubmitField('earn stamp')
    def __init__(self, badge_name, *args, **kwargs):
        super(EarnStampsForm, self).__init__(*args, **kwargs)
        self.badge_name = badge_name

class RemoveOldAccountsForm(FlaskForm):
    years = SelectField('Years Inactive:', choices=[(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5'),(6,'6'),(7,'7'),(8,'8'),(9,'9'),(10,'10')], coerce=int)
    submit = SubmitField('Delete Old Accounts')

class ResetDateForm(FlaskForm):
 
    reset_date = DateField('reset date', format='%m-%d', validators=[DataRequired()])
    submit = SubmitField('Change Reset Date')
    
class BadgePointsForm(FlaskForm):
    level1_points = IntegerField('level 1 points', validators=[positive])
    level2_points = IntegerField('level 2 points', validators=[Optional(), positive])
    level3_points = IntegerField('level 3 points', validators=[Optional(), positive])
    level4_points = IntegerField('level 4 points', validators=[Optional(), positive])
    level5_points = IntegerField('level 5 points', validators=[Optional(), positive])
    level6_points = IntegerField('level 6 points', validators=[Optional(), positive])
    level7_points = IntegerField('level 7 points', validators=[Optional(), positive])
    level8_points = IntegerField('level 8 points', validators=[Optional(), positive])
    level9_points = IntegerField('level 9 points', validators=[Optional(), positive])
    level10_points = IntegerField('level 10 points', validators=[Optional(), positive])
    submit = SubmitField('Change Badge Points') 
           
    def validate(self):       
        result = True 
        # Check normal validation
        if not FlaskForm.validate(self):
            result = False     
            
        # Make sure that a levels points are not less than the level before it (unless it is set to None)
        previous_points = self.level1_points.data      
        for field in [self.level2_points, self.level3_points, self.level4_points, self.level5_points, self.level6_points, self.level7_points, self.level8_points, self.level9_points, self.level10_points]:           
            if field.data:
                if previous_points == None:
                    field.errors.append('This level cannot have points if the previous level does not have points.')
                    result = False
                elif field.data <= previous_points:
                    field.errors.append('The points for this level cannot be less than the points for the previous level.')
                    result = False
                               
            previous_points = field.data
        return result
