# MIT License
# MESA © 2019
# PSU Capstone 2018-2019

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

class NonValidatingSelectField(SelectField):
    """
    Attempt to make an open ended select multiple field that can accept dynamic
    choices added by the browser.
    """
    def pre_validate(self, form):
        pass

class RegistrationForm(FlaskForm):

    firstname = StringField('Firstname', validators=[DataRequired()])
    lastname = StringField('Lastname', validators=[DataRequired()])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    school = SelectField('School', coerce=int, choices=School.get_all_schools_names())
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, message="your password must be at least %(min)d characters long!")
                                 , Regexp("^(?=.*[0-9])(?=.*[!@#\$%\^&\*])",
                                          message="The string must contain at least one numeric digit and one symbol!")])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        if User.get_user_by_email(email.data):
            raise ValidationError('That email is already taken. Please choose a different one.')

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
            raise ValidationError('There is no account with that email. You must register with it first.')

class RequestResetUserForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Request Username')

    def validate_email(self, email):
        user = User.validate_email(email)
        if user == False:
            raise ValidationError('There is no account with that email. You must register with it first.')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password',  validators=[DataRequired(), Length(min=8, message="your password must be at least %(min)d characters long!")
                                 , Regexp("^(?=.*[0-9])(?=.*[!@#\$%\^&\*])",
                                          message="The string must contain at least one numeric digit and one symbol!")])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class UpdateEmailForm(FlaskForm):

    email = StringField('Email', validators=[Email()])
	
    submit = SubmitField('Update Email')
    
    def validate_email(self, email):
        if User.get_user_by_email(email.data):
            raise ValidationError('That email is already taken. Please choose a different one.')

class UpdateNameForm(FlaskForm):

    firstname = StringField('Firstname')
    lastname = StringField('Lastname')

    submit = SubmitField('Update Name')

class UpdateSchoolForm(FlaskForm):

    school = SelectField('School', coerce=int, choices=School.get_all_schools_names())

    submit = SubmitField('Update School')

class AddSchoolForm(FlaskForm):

    schoolName = StringField('SchoolName', validators=[DataRequired()])

    submit = SubmitField('Add School')

    def validate_schoolName(self, schoolName):
        if School.get_school_by_name(schoolName.data):
            raise ValidationError('That school already exists.')

class DeleteSchoolForm(FlaskForm):

    school = SelectField('School', coerce=int, choices=School.get_all_schools_names())

    submit = SubmitField('Delete School')
    def validate_school(self, school):
        schoolName = School.get_school_by_id(school.data)
        if schoolName.school_name == 'Other':
            raise ValidationError('You cannot delete \'Other\'')

class UpdatePasswordForm(FlaskForm):
    old_password = PasswordField('Password')
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8,
                                                                            message="your password must be at least %(min)d characters long!")
        , Regexp("^(?=.*[0-9])(?=.*[!@#\$%\^&\*])",
                 message="The string must contain at least one numeric digit and one symbol!")])
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


class AddStampForm(FlaskForm):

    badge = SelectField('Badge', coerce=int, choices=Badge.get_all_badges_id_with_names())
    stamp_name = StringField('Stamp Name', validators=[DataRequired()])
    points = IntegerField('Points', validators=[DataRequired(), positive])
    submit = SubmitField('Add Stamp')

    def validate_stamp_name(self, stamp_name):
        if Stamp.get_stamp_by_name(stamp_name.data):
            raise ValidationError('A stamp already exists with that name!')

class DeleteStampForm(FlaskForm):

    badgedelete = SelectField('Badge', coerce=int, choices=Badge.get_all_badges_id_with_names())
    stampdelete = NonValidatingSelectField('Stamp', choices={})
    submitdelete = SubmitField('Delete Stamp')


class RemoveOldAccountsForm(FlaskForm):
    years = SelectField('Years Inactive:', choices=[(10,'10'),(9,'9'),(8,'8'),(7,'7'),(6,'6'),(5,'5'),(4,'4'),(3,'3'),(2,'2'),(1,'1')], coerce=int)
    submit = SubmitField('Delete Old Accounts')

class ResetDateForm(FlaskForm):
 
    reset_date = DateField('reset date', format='%m-%d', validators=[DataRequired()])
    submit = SubmitField('Change Reset Date')
class EditBadgeForm(FlaskForm):

    badge = SelectField('Badge', coerce=int, choices=Badge.get_all_badges_id_with_names())
    badgeName = StringField('badgeName', validators=[DataRequired()])
    submit = SubmitField('Update Badge')


class BadgeForm(FlaskForm):

    badge = SelectField('Badge', coerce=int, choices=Badge.get_all_badges_id_with_names())
    submit = SubmitField('Update Badge')

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

