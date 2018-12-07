"""
Modified from CoreyMSchafer's Flask Tutorial
https://github.com/CoreyMSchafer/code_snippets/blob/master/Python/Flask_Blog/06-Login-Auth/flaskblog/routes.py
"""
from flask import render_template, url_for, flash, redirect, request
from MESAeveryday import app, bcrypt
from MESAeveryday.forms import RegistrationForm, LoginForm
from MESAeveryday.models import User, db_model
from flask_login import login_user, current_user, logout_user, login_required

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
        db = db_model()
        db.add_user(form_register.username.data, form_register.firstname.data, form_register.lastname.data, 
                    form_register.email.data, 'default.jpg', hashed_password, form_register.school.data)
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('landpage'))
    return render_template('landpage.html', title='Landing', form_l=form_login, form_r=form_register)
		
@app.route("/login", methods=['GET', 'POST'])
def login():
    # Login Form Submitted
    form_register = RegistrationForm()
    form_login = LoginForm()
    if form_login.validate_on_submit():
        db = db_model()
        data = db.get_user_by_username(form_login.username.data)
        if data and bcrypt.check_password_hash(data[0][6], form_login.password.data):
            user = User(data[0][0], data[0][1], data[0][2], data[0][3], data[0][4], data[0][6], data[0][7], data[0][8])
            login_user(user, remember=form_login.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('landpage.html', title='Landing', form_l=form_login, form_r=form_register)

@app.route("/dashboard", methods=['GET','POST'])
@login_required
def dashboard():
    result = ''
    db = db_model()
    result = db.view_badge()
    return render_template('dashboard.html', result = result)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('landpage'))

