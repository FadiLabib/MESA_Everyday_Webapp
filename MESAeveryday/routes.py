"""
This file contains all the routes used by the MESA Everyday application.
Each route selects the proper forms for each page, calculates the data to put in the page, and renders the html for that page

Modified from CoreyMSchafer's Flask Tutorial
https://github.com/CoreyMSchafer/code_snippets/blob/master/Python/Flask_Blog/06-Login-Auth/flaskblog/routes.py
"""
from flask import render_template, url_for, flash, redirect, request
from MESAeveryday import app, bcrypt, mail
from MESAeveryday.forms import RegistrationForm, LoginForm, RequestResetForm, RequestResetUserForm, ResetPasswordForm, EarnStampsForm, UpdateEmailForm, UpdateNameForm, UpdateSchoolForm, UpdatePasswordForm, RemoveOldAccountsForm
from MESAeveryday.models import User, School, Badge, Stamp, UserStamp, Avatar
from MESAeveryday.calendar_events import get_event_list, searchEvents, get_mesa_events
from flask_login import login_user, current_user, logout_user, login_required, login_manager
from flask_mail import Message
from datetime import datetime
import secrets
import os


@app.route("/", methods=['GET', 'POST'])
@app.route("/landpage", methods=['GET', 'POST'])
def landpage():
    """
      Default landing page for the website
      Consists of both the registration form and the login form
    """
    
    form_register = RegistrationForm()
    form_login = LoginForm()
    return render_template('landpage.html', title='Landing', form_l=form_login, form_r=form_register)


@app.route("/register", methods=['GET', 'POST'])
def register():
    """
      Route that processes a registration request
      After the registration is processes, it renders the landing page
    """   
    
    form_register = RegistrationForm()
    form_login = LoginForm()
    
    # If the registration form is submitted and their are no errors in the form, try to register the user
    if form_register.validate_on_submit():  
    
        # Generate username
        new_username = generate_username(form_register.firstname.data, form_register.lastname.data, random_code())
       
        if new_username == 'ERROR':
            flash('Sorry, we were unable to generate an account for you.', 'danger')
        else:
            # Generate hashed password
            hashed_password = bcrypt.generate_password_hash(form_register.password.data).decode('utf-8')
            
            # Add user to the database
            new_user = User(new_username, form_register.firstname.data, form_register.lastname.data,
                            form_register.email.data, hashed_password, form_register.school.data)
            User.add_new_user(new_user)

            # Tell the user their new username and send them an email with the username
            flash('Your account has been created! You are now able to log in with the username: ' + new_username, 'success')
            send_generate_username(form_register.email.data, new_username)

    return render_template('landpage.html', title='Landing', form_l=form_login, form_r=form_register)

@app.route("/login", methods=['GET', 'POST'])
def login():
    """
      Route that processes a login attempt
      If the login is a success they are taken to either the page they last attempted to visit or the dashboard
      If the login fails, the landing page is rendered
    """   
    
    form_register = RegistrationForm()
    form_login = LoginForm()
    
    # If the login form is submitted and their are no errors in the form, try to log them in
    if form_login.validate_on_submit():
        user = User.get_user_by_username(form_login.username.data)
        
        # User entered the correct credentials
        if user and bcrypt.check_password_hash(user.password, form_login.password.data):
            User.update_last_login(user.id, datetime.now())
            login_user(user, remember=form_login.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            
        # User did not enter the correct credentials
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
            
    return render_template('landpage.html', title='Landing', form_l=form_login, form_r=form_register)


@app.route("/dashboard", methods=['GET', 'POST'])
@login_required
def dashboard():
    """
        Page that displays summary information about a student's progress
        This is the default page a user is taken to when they log in
    """   
    
    # Send admins to the admin page
    if (User.verify_role(current_user.id)):
        return redirect(url_for('admin'))
        
    # Get all the badges
    badges = Badge.get_all_badges_id_with_names()
    badge_names, badge_ids = [row.badge_name for row in badges], [row.badge_id for row in badges]
    
    # Get the total amount of points the user has for each badge
    all_badge_points = []  
    for badge_id in badge_ids:
        badge_progress = User.get_badge_progress(current_user.id, badge_id)
        if badge_progress:
            badge_points = badge_progress[0]
        else:
            badge_points = 0
        all_badge_points.append(badge_points)

    # Call the google api and pull all upcoming events
    events = get_event_list()
    
    # Parse the events into incoming and special groups
    mesa_days = searchEvents(events, ['Mesa','Day'])
    other_days = searchEvents(events, ['Mesa','Day'])
    upcoming_events = [event for event in events if event['remain_days'] < 7]
    mesa_events = get_mesa_events(events)

    user_id = current_user.id 
    # Get the user's progress on the badge
    badge_progress = User.get_badge_progress(user_id, badge_id)
    if badge_progress:
        points = badge_progress[0]
        current_level = badge_progress[1]
        to_next_lv = badge_progress[2]
    else:
        points = 0
        current_level = 0
        to_next_lv = 0
        
    return render_template('dashboard.html',
                           events=events,
                           number_upcoming=len(upcoming_events),
                           upcoming_events=upcoming_events,
                           result=zip(badge_names, badge_ids),
                           mesa_days=mesa_days,
                           mesa_events=mesa_events,
                           other_days=other_days,
                           points=zip(badge_names, all_badge_points),
                           pt=points, 
                           lv=current_level, 
                           to_next_lv=to_next_lv)


@app.route("/events", methods=['GET', 'POST'])
# @login_required
def events():
    """
        Page that displays summary information about a student's progress
        This is the default page a user is taken to when they log in
    """   
    
    # Send admins to the admin page
    if (User.verify_role(current_user.id)):
        return redirect(url_for('admin'))
        
    # Get all the badges
    badges = Badge.get_all_badges_id_with_names()
    badge_names, badge_ids = [row.badge_name for row in badges], [row.badge_id for row in badges]
    
    # Get the total amount of points the user has for each badge
    all_badge_points = []  
    for badge_id in badge_ids:
        badge_progress = User.get_badge_progress(current_user.id, badge_id)
        if badge_progress:
            badge_points = badge_progress[0]
        else:
            badge_points = 0
        all_badge_points.append(badge_points)

    # Call the google api and pull all upcoming events
    events = get_event_list()
    
    # Parse the events into incoming and special groups
    mesa_days = searchEvents(events, ['Mesa','Day'])
    other_days = searchEvents(events, ['Mesa','Day'])
    upcoming_events = [event for event in events if event['remain_days'] < 7]
    mesa_events = get_mesa_events(events)

    return render_template('events.html',
                           events=events,
                           number_upcoming=len(upcoming_events),
                           upcoming_events=upcoming_events,
                           result=zip(badge_names, badge_ids),
                           mesa_days=mesa_days,
                           mesa_events=mesa_events,
                           other_days=other_days,
                           points=zip(badge_names, all_badge_points))


@app.route("/logout")
def logout():
    """
        Route that logs a user out and sends them to the landing page
        Can be accessed anywhere on the site once a user has logged in
    """   
    logout_user()
    return redirect(url_for('landpage'))


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    """
        Page for users who are not logged on to request a password reset  
        Sends an email to the user with a link to a password reset page if they enter a valid email
    """   
    # Send user to the dashboard if they are logged in. This page is intended for those who forgot their password
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = RequestResetForm()

    # If the user has submitted the form with a valid email, send them an email with a link to the reset password page
    if form.validate_on_submit():
        user = User.get_user_by_email(form.email.data)
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('landpage'))

    return render_template('reset_request.html', title='Rest Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    """
        Page for users to reset their password
        Will not work if the route does not contain a valid token 
        This page can only be reached via an email sent to the user
    """      
    # Send user to the dashboard if they are logged in. This page is intended for those who forgot their password
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    # Verify that the token is valid and has not expired
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('landpage'))

    form = ResetPasswordForm()
    
    # If the form has been submitted and is valid, reset their paassword
    if form.validate_on_submit():
    
        # Hash the new password that the user has chosen
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
      
        # Reset the password. If it updates correctly, tell the user that their password was updated
        if User.reset_pwd(user.id, hashed_password) == True:
            flash('Your password has been updated! You are now able to log in', 'success')
            return redirect(url_for('landpage'))
        # If the password didn't update correctly, tell the user that it failed
        else:
            flash('Sorry, we were unable to update your password', 'danger')
            return redirect(url_for('landpage'))
    return render_template('reset_token.html', title='Rest Password', form=form)


@app.route("/forgot_username", methods=['GET', 'POST'])
def forgot_username():
    """
        Page for users to request a reminder of their username
        Usernames are generated at registration and are unchangeable
        Sends an email to a user with their username if they enter a valid email
    """     
    # Send user to the dashboard if they are logged in. This page is intended for those who forgot their username
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    form = RequestResetUserForm()
    
    # If the form has been submitted and is valid, send the user an email with their username
    if form.validate_on_submit():
        user = User.get_user_by_email(form.email.data)
        send_forgot_username(user)
        flash('An email has been sent with your username.', 'info')
        return redirect(url_for('landpage'))
    return render_template('forgot_username.html', title='Rest User', form=form)
    
   
@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    """
        Page for users to change their account information
        Page is broken up into separate forms for each section, so they can only update their account one piece at a time
    """    
    emailform = UpdateEmailForm()
    nameform = UpdateNameForm()
    schoolform = UpdateSchoolForm()
    passwordform= UpdatePasswordForm()
    avatars = ""
    myaccount = User.get_user_by_username(current_user.username)

	#Update password
    if passwordform.password.data and passwordform.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(passwordform.password.data).decode('utf-8')
        if User.reset_pwd(myaccount.id, hashed_password) == True:
            flash('Your account has been successfully updated!', 'success')
        else:
            flash('Sorry, we were unable to update your account', 'danger')
        return redirect(url_for('account'))

	#Update email
    if emailform.email.data and emailform.validate_on_submit():
        if User.update_email(myaccount.id, emailform.email.data) == True:
            flash('Your account has been successfully updated!', 'success')
        else:
            flash('Sorry, we were unable to update your account', 'danger')
        return redirect(url_for('account'))

	#Update name
    if (nameform.firstname.data or nameform.lastname.data) and nameform.validate_on_submit():
        if User.update_name(myaccount.id, nameform.firstname.data, nameform.lastname.data) == True:
            flash('Your account has been successfully updated!', 'success')
        else:
            flash('Sorry, we were unable to update your account', 'danger')
        return redirect(url_for('account'))

    #Update school
    if schoolform.school.data and schoolform.validate_on_submit():
        if User.update_school(myaccount.id, schoolform.school.data) == True:
            flash('Your account has been successfully updated!', 'success')
        else:
            flash('Sorry, we were unable to update your account', 'danger')
        return redirect(url_for('account'))

    #Update avatar
    if request.method=='POST':
        avatarSelect = request.form.get('avatarSelect')
        if avatarSelect:
            if User.update_avatar(myaccount.id, avatarSelect) == True:
                flash('Your account has been successfully updated!', 'success')
            else:
                flash('Sorry, we were unable to update your account', 'danger')
            return redirect(url_for('account'))

    #Load page
    if request.method =='GET':
        emailform.email.data = current_user.email
        nameform.firstname.data = current_user.first_name
        nameform.lastname.data = current_user.last_name
        schoolform.school.data = current_user.school_id

    # Get all the badges
    badges = Badge.get_all_badges_id_with_names()
    badge_names, badge_ids = [row.badge_name for row in badges], [row.badge_id for row in badges]

    # Call the google api and pull all upcoming events
    events = get_event_list()
    
    # Parse the events into incoming and special groups
    mesa_days = searchEvents(events, ['Mesa','Day'])
    other_days = searchEvents(events, ['Mesa','Day'])
    upcoming_events = [event for event in events if event['remain_days'] < 7]
        
    return render_template('account.html', title='Account', avatar_files=Avatar.get_all_avatars(), form_email=emailform, form_name=nameform, form_password=passwordform, form_school=schoolform, result=zip(badge_names, badge_ids), events=events,
                           number_upcoming=len(upcoming_events), upcoming_events=upcoming_events, mesa_days=mesa_days,
                           other_days=other_days)

@app.route("/account_deactivate", methods=['GET', 'POST'])
@login_required
def account_deactivate():
    myaccount = User.get_user_by_username(current_user.username)
    print(myaccount.id)
    if current_user.is_authenticated:
        if request.method=='POST':
            firstName=request.form.get('FirstName')
            lastName=request.form.get('LastName')

            if ((firstName.lower()==current_user.first_name.lower())
                    and (lastName.lower()==current_user.last_name.lower())):
                print(request.form.get('FirstName'))
                User.delete_user_by_id(myaccount.id)
                logout_user()
                return redirect(url_for('landpage'))
            else :
                flash('Account does not match. Please check First Name and Last Name!!', 'danger')
        return render_template('account_deactivate.html')




@app.route("/earn_stamps", methods=['GET', 'POST'])
@login_required
def earn_stamps():
    """
        Page for users earn stamps
        Users pick a stamp and enter they date they accomplished the task
        The stamp will be added to the user's account and does not do any verification
            as to whether or not they actually did the task
    """  

    # Get all badge names
    badge_names = [row.badge_name for row in Badge.get_all_badges_names()]   

    # A dictionary that maps badge_ids to badge_name
    badges = {row.badge_id : row.badge_name for row in Badge.get_all_badges_id_with_names()}.items()    
    
    forms, t = [], 1       # several pairs of forms (stamp, date, submit). t is used to assign unique id
    for badge in badges:
        stamps = Stamp.get_stamps_of_badge(badge[0])

        if stamps.first() is not None:
            form = EarnStampsForm(badge[1], prefix=badge[1])    # create a pair of form. prefix -> make each form unique

            form.time_finished.id = "date" + str(t)             # to create an unique id without space, slash, etc...
                                                                # HTML doesnt seem to be friendly to an id with space(s), sigh

            form.stamps.choices = stamps                      # assign unearned stamps to the select field
            forms.append(form)                                  # create a list of forms
            t += 1
    for form in forms:
        if form.submit.data:
            if form.validate_on_submit():
                id = current_user.id    # acquire the user_id of current user
                if UserStamp.earn_stamp(id, form.stamps.data, datetime.now(), form.time_finished.data.strftime('%Y-%m-%d')) == True:
                    # flash('You've earned a new stamp!', 'success')
                    # some message should be shown here, flash doesnt work
                    print('successfully added.')
                # else:
                    # flash('Failed adding stamp', 'warning')
                    # some message should be shown here, flash doesnt work
                return redirect('/dashboard')   # could be redirected to either dashboard or the same page?

    # Get all the badges
    badges = Badge.get_all_badges_id_with_names()
    badge_names, badge_ids = [row.badge_name for row in badges], [row.badge_id for row in badges]

    # Call the google api and pull all upcoming events
    events = get_event_list()
    
    # Parse the events into incoming and special groups
    mesa_days = searchEvents(events, ['Mesa','Day'])
    other_days = searchEvents(events, ['Mesa','Day'])
    upcoming_events = [event for event in events if event['remain_days'] < 7]

    return render_template('earnstamps.html', title='Earn Stamps', forms=forms, result=zip(badge_names, badge_ids), events=events,
                           number_upcoming=len(upcoming_events), upcoming_events=upcoming_events, mesa_days=mesa_days,
                           other_days=other_days)

@app.route("/badges/<badge_id>", methods=['GET', 'POST'])
@login_required
def check_badge(badge_id):
    """
        Page for checking a user's progress on an individual badge
        The particular badge being view is passed in through the route
    """  
    
    # Get all badges 
    badges = Badge.get_all_badges_id_with_names()
    badge_names, badge_ids = [row.badge_name for row in badges], [row.badge_id for row in badges]

    # Call the google api and pull all upcoming events
    events = get_event_list()
    
    # Parse the events into incoming and special groups
    mesa_days = searchEvents(events, ['Mesa','Day'])
    other_days = searchEvents(events, ['Mesa','Day'])
    upcoming_events = [event for event in events if event['remain_days'] < 7]
    
    # Get the name and picture of the page currently being viewed
    badge_name = Badge.get_badge_name(badge_id).first()[0]
    picture_file = Badge.get_badge_picture(badge_id).first()[0]
    
    # Get the id of current user and separate the stamps that they have earned from the one's they have not earned
    user_id = current_user.id    
    unearned_stamps = [row.stamp_name for row in Stamp.get_unearned_stamps_of_badge(user_id, badge_id)]     
    earned_stamps = [row for row in UserStamp.get_earned_stamps_of_badge(user_id, badge_id)]
    
    # If all the stamps for this badge have been earned, print this instead
    if not unearned_stamps:
        unearned_stamps = ['All stamps earned'] 
    
    # Get the user's progress on the badge
    badge_progress = User.get_badge_progress(user_id, badge_id)
    if badge_progress:
        points = badge_progress[0]
        current_level = badge_progress[1]
        to_next_lv = badge_progress[2]
    else:
        points = 0
        current_level = 0
        to_next_lv = 0

    # process on deleting stamp
    if request.method == 'POST':
        stamp_id = request.form.get('stamp_id')
        time_finished = datetime.strptime(request.form.get('time_finished'), '%Y-%m-%d').date()
        log_date = datetime.strptime(request.form.get('log_date'), '%Y-%m-%d %H:%M:%S')
        if stamp_id and time_finished and log_date:
            if UserStamp.delete_stamp(user_id, stamp_id, time_finished, log_date):
                print('deleted:\nid: ' + str(stamp_id) + '\ntime finished: ' +  str(time_finished) + '\nlog_date: ' + str(log_date))
            else:
                print('error when deleting user earned stamp')
        return redirect('/badges/' + str(badge_id))
    
    return render_template('badges.html', result=zip(badge_names, badge_ids), badge_name=badge_name, unearned=unearned_stamps, earned=earned_stamps, pt=points, lv=current_level, to_next_lv=to_next_lv, picture_file=picture_file, badge_id=badge_id, events=events,
                           number_upcoming=len(upcoming_events), upcoming_events=upcoming_events, mesa_days=mesa_days,
                           other_days=other_days)


def random_code():
    """
        Generates a random 3 digit code 
        Returns the code as a 3 character long string
    """  
    import random
    x=random.randint(000,999)
    if x<10:
        x= '0'+str(x)+'0'
    else:
        if x>=10 and x<100:
            x= '0'+str(x)

    return x

def generate_username(first_name, last_name, random_code):
    """
        Generates a username based on the users first name, last name, and a randomly generated 3 digit code
        outputs a string that contains the generated username
        
        input:
            first_name : string
            last_name : string
            random_code : string    
    """      
    if len(first_name) > 8 and len(last_name)>8:
        generated_name = first_name[0:8].lower() + last_name[0:8].lower() + str(random_code)
    else:
        if len(first_name)>8:
            generated_name = first_name[0:8].lower() + last_name.lower() +str(random_code)
        else:
            if len(last_name)>8:
                generated_name =  first_name.lower() + last_name[0:8].lower() +str(random_code)
            else:
                generated_name =  first_name.lower()+last_name.lower()+str(random_code)
                    
    generated_name = check_username(generated_name)
    return generated_name
    
def check_username(generated_username):
    """
        Checks to see if the username is already taken. If it is, add 1 to the 3 digit code (it repeats this until it finds an unused code)
        It returns the original username if it is not taken, and returns the new username if it is taken
        If all 1000 possible usernames are taken, it will return 'ERROR'
        
        input:
            generated_username : string         
    """  
    global match
    match = False
    new_username = generated_username
    all_usernames = [row.username for row in User.get_all_username()]
    
    # Check if username is taken
    for username in all_usernames:
        if username == generated_username:
            match = True
            break

    # If the username is taken, generate a new code
    if match:
        randnumberstring = new_username[(len(new_username) - 3):(len(new_username) + 1)]
        randnumber = int(randnumberstring)
        number_of_matches = 1

        # Add 1 to the 3 digit code until we find an unused code
        while match:

                # If we've tried every possible code, return 'ERROR'
                if number_of_matches == 1000:
                    return 'ERROR'

                # Loop back to 000 if the code is 999
                if randnumber == 999:
                    randnumberstring = '000'
                # Otherwise add 1 to the code
                else:
                    randnumber = randnumber + 1
                    randnumberstring = str(randnumber)
                    if randnumber < 10:
                        randnumberstring = '00' + str(randnumber)
                    if (randnumber >= 10) and (randnumber < 100):
                        randnumberstring = '0' + str(randnumber)

                #Create the new username
                new_username = (new_username[0:len(new_username) - 3]+ str(randnumberstring))
                match = False

                # Check to make sure the new username isn't already in use
                for username in all_usernames:
                    if username == new_username:
                        randnumber = int(randnumberstring)
                        match = True
                        number_of_matches += 1
                        break

    return new_username

def send_reset_email(user):
    """
        Sends an email to a user with a link to reset their password
        
        input:
            user : User object
    """
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)

def send_forgot_username(user):
    """
        Sends an email to a user with their username
        
        input:
            user : User Object
    """
    msg = Message('Username Reminder',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''Hi '''+user.first_name+'''\nYour username is ''' + user.username
    mail.send(msg)
    
def send_generate_username(user_email, username):
    """
        Sends the generated username to an account
        
        input:
            user_email : string
            username : string
    """
    msg = Message('Account Created',
                  sender='noreply@demo.com',
                  recipients=[user_email])
    msg.body = f'''Thank you for registering an account with Oregon MESA your unique
username has been generated and it is '''+username+'''
please keep this email handy as you will need that username every time you
login to the app. '''
    mail.send(msg)

# Added by Millen
# Load admin page if role is admin
@app.route("/admin")
@login_required
def admin():
    # https://stackoverflow.com/questions/21895839/restricting-access-to-certain-areas-of-a-flask-view-function-by-role
    if not User.verify_role(current_user.id):
        return redirect(url_for('dashboard'))
        
    # Top scores will be a dictionary of arrays. 
    # Each array holds all the users and top scores for a specific badge
    # The dictionary will be for each badge and is indexed based on the badge id
    top_scores = {}    
        
    # Get all badges
    badges = Badge.get_all_badges()
    
    # Get all the top scores/users for each badge
    for badge in badges:
        # Find out what the top three scores are
        top_badge_scores = Badge.get_top_scores(badge.badge_id)
        record_holders = []
        
        # For each top score, get all the users that have that score        
        for top_score in top_badge_scores:
            # Add each user with a top score to and array of users/top scores
            users_with_top_score = User.get_record_holders(badge.badge_id, top_score.total_points)
            for user in users_with_top_score:
                record_holders.append(user)
        # Add the array of users/top scores to the total list of scores (indexed by the badge id)
        top_scores[badge.badge_id] = record_holders
    
    
    return render_template('admin.html', badges=badges, top_scores=top_scores)

@app.route("/admin_control", methods=['GET', 'POST'])
@login_required    
def admin_control():
    if not User.verify_role(current_user.id):
        return redirect(url_for('dashboard'))
        
    emailform = UpdateEmailForm()
    passwordform = UpdatePasswordForm()
    oldaccountsform = RemoveOldAccountsForm()
    admin_account = User.get_user_by_username(current_user.username)

	#Update password
    if passwordform.password.data and passwordform.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(passwordform.password.data).decode('utf-8')
        if User.reset_pwd(admin_account.id, hashed_password) == True:
            flash('Your account has been successfully updated!', 'success')
        else:
            flash('Sorry, we were unable to update your account', 'danger')
        return redirect(url_for('admin_control'))

	#Update email
    if emailform.email.data and emailform.validate_on_submit():
        if User.update_email(admin_account.id, emailform.email.data) == True:
            flash('Your account has been successfully updated!', 'success')
        else:
            flash('Sorry, we were unable to update your account', 'danger')
        return redirect(url_for('admin_control'))
        
    #Remove old accounts
    if oldaccountsform.years.data and oldaccountsform.validate_on_submit():
     
        results = User.delete_innactive_accounts(oldaccountsform.years.data)
        if results:
            flash('Successfully removed ' + str(results) + ' account(s)!', 'success')
        else:
            flash('No accounts were deleted', 'success')
        return redirect(url_for('admin_control'))

    #Load page
    if request.method =='GET':
        emailform.email.data = current_user.email
      
    return render_template('admin_control.html', form_email=emailform, form_password=passwordform, form_old_accounts=oldaccountsform)    
        


@app.route("/admin_settings", methods=['GET', 'POST'])
@login_required
def admin_settings():
    """
        Page for admin to control various parts of the application
        Admins can add or remove schools, remove old accounts, set academic year, and manage the admin account
        Only those will a valid admin account can view this page
    """    

    if not User.verify_role(current_user.id):     
        return redirect(url_for('dashboard'))

    return render_template('admin_settings.html')