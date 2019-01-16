"""
Modified from CoreyMSchafer's Flask Tutorial
https://github.com/CoreyMSchafer/code_snippets/blob/master/Python/Flask_Blog/06-Login-Auth/flaskblog/routes.py
"""
from flask import render_template, url_for, flash, redirect, request
from MESAeveryday import app, bcrypt, mail
from MESAeveryday.forms import RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm
from MESAeveryday.models import User, Role, UserRole, School, Badge, Stamp, UserStamp, loadSession
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

from MESAeveryday.calendar_events import get_event_list, searchEvents

@app.route("/", methods=['GET', 'POST'])
# Millen's Added code for a merged landing page
@app.route("/landpage", methods=['GET', 'POST'])
def landpage():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form_register = RegistrationForm()
    form_login = LoginForm()
    return render_template('landpage.html', title='Landing', form_l=form_login, form_r=form_register)


@app.route("/register", methods=['GET', 'POST'])
def register():
    # Registration Form Submitted
    form_register = RegistrationForm()
    form_login = LoginForm()
    if form_register.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form_register.password.data).decode('utf-8')
        new_user = User(form_register.username.data, form_register.firstname.data, form_register.lastname.data,
                        form_register.email.data, hashed_password, form_register.school.data)
        session = loadSession()
        session.add(new_user)
        session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('landpage'))
    return render_template('landpage.html', title='Landing', form_l=form_login, form_r=form_register)


@app.route("/login", methods=['GET', 'POST'])
def login():
    # Login Form Submitted
    form_register = RegistrationForm()
    form_login = LoginForm()
    if form_login.validate_on_submit():
        session = loadSession()
        user = session.query(User).filter(User.username == form_login.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form_login.password.data):
            login_user(user, remember=form_login.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('landpage.html', title='Landing', form_l=form_login, form_r=form_register)


@app.route("/dashboard", methods=['GET', 'POST'])
@login_required
def dashboard():
    session = loadSession()
    result = [row.badge_name for row in session.query(Badge.badge_name)]

    # # call the google api and pull all upcoming events
    events = get_event_list()
    # # parse the events into incoming and special groups
    mesa_days = searchEvents(events, ['Mesa','Day'])
    other_days = searchEvents(events, ['Mesa','Day'])
    upcoming_events = [event for event in events if event['remain_days'] < 7]

    return render_template('dashboard.html',
                           events=events,
                           number_upcoming=len(upcoming_events),
                           upcoming_events=upcoming_events,
                           result=result,
                           mesa_days=mesa_days,
                           other_days=other_days,)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('landpage'))

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)

@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = RequestResetForm()

    if form.validate_on_submit():
        session = loadSession()
        user = session.query(User).filter(User.email == form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('landpage'))

    return render_template('reset_request.html', title='Rest Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    user = User.verify_reset_token(token)

    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('landpage'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        #this is the new password that the user has chosen
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        print("Original: ", user.password)
        #updating the password requires first loading a new session 
        session = loadSession()
        #once a session is loaded we want to get the row 
        #where User.id matches the id of the user returned by User.verify_reset_token(token)
        #this insures that the password for the correct user will be the one changed
        row = session.query(User).filter(User.id==user.id).first()
        #Change the password is a simple assign statement
        row.password = hashed_password
        #Changes need to be committed in order to make it to the database
        session.commit()
        #send a message to the user telling them that there account has been updated successfully
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('landpage'))
    return render_template('reset_token.html', title='Rest Password', form=form)
