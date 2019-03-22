"""
This file contains all the routes used by the MESA Everyday application.
Each route selects the proper forms for each page, calculates the data to put in the page, and renders the html for that page

Modified from CoreyMSchafer's Flask Tutorial
https://github.com/CoreyMSchafer/code_snippets/blob/master/Python/Flask_Blog/06-Login-Auth/flaskblog/routes.py
"""
from MESAeveryday import app, bcrypt, mail, limiter
from flask import render_template, url_for, flash, redirect, request,jsonify
from MESAeveryday.forms import RegistrationForm, LoginForm, RequestResetForm, RequestResetUserForm, ResetPasswordForm, EarnStampsForm, UpdateEmailForm, UpdateNameForm, UpdateSchoolForm, \
    UpdatePasswordForm,AddSchoolForm,DeleteSchoolForm,AddStampForm,DeleteStampForm,UpdatePasswordForm, RemoveOldAccountsForm, ResetDateForm,EditBadgeForm,BadgePointsForm

from MESAeveryday.models import User, School, Badge, Stamp, UserStamp, Avatar, Reset_Date, Icon, close_session

from MESAeveryday.calendar_events import get_event_list, searchEvents, get_mesa_events

from flask_login import login_user, current_user, logout_user, login_required, login_manager
from flask_mail import Message
from datetime import datetime
import secrets
import os
    



'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                            Universal Routes
                These routes are used by both admins and users
                   Typically, they involve account management
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


@app.route("/", methods=['GET', 'POST'])
@app.route("/landpage", methods=['GET', 'POST'])
def landpage():
    """
      Default landing page for the website
      Consists of both the registration form and the login form
    """
    
    try:
        # Send user to the dashboard if they are logged in. This page is intended for those who have not logged in yet
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form_register = RegistrationForm()
        form_login = LoginForm()
        close_session()
        return render_template('landpage.html', 
                               title='Landing', 
                               form_l=form_login, 
                               form_r=form_register)
    except:

        return redirect(url_for('error'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    """
      Route that processes a registration request
      After the registration is processes, it renders the landing page
    """ 
    try:
        # Send user to the dashboard if they are logged in. Users shouldn't be able to create accounts while logged in
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        form_register = RegistrationForm()
        form_login = LoginForm()

        # If the registration form is submitted and their are no errors in the form, try to register the user
        if form_register.validate_on_submit():  

            # Generate username
            new_username = generate_username(form_register.firstname.data, form_register.lastname.data, random_code())
           
            if new_username == 'ERROR':
                flash('Sorry, we were unable to generate an account for you!', 'danger')
            else:
                # Generate hashed password
                hashed_password = bcrypt.generate_password_hash(form_register.password.data).decode('utf-8')
                
                # Add user to the database
                new_user = User(new_username, form_register.firstname.data, form_register.lastname.data,
                                form_register.email.data, hashed_password, form_register.school.data)
                User.add_new_user(new_user)

                # Tell the user their new username and send them an email with the username
                flash('Your account has been created! You are now able to log in with the username: ' + new_username + '!', 'success')
                send_generate_username(form_register.email.data, new_username)
        close_session()
        return render_template('landpage.html', 
                               title='Landing', 
                               form_l=form_login, 
                               form_r=form_register)
    except:
        return redirect(url_for('error'))      

@app.route("/login", methods=['GET', 'POST'])
@limiter.limit ('50 per hour')
def login():
    """
        Route that processes a login attempt
        If the login is a success they are taken to either the page they last attempted to visit or the dashboard
        If the login fails, the landing page is rendered
    """
    
    try:
        # Send user to the dashboard if they are logged in. This page is intended for those who haven't logged in yet
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
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
                limiter.reset()
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
                
            # User did not enter the correct credentials
            else:
                flash('Login unsuccessful. Please check your username and password!', 'danger')
        close_session()
        return render_template('landpage.html', 
                               title='Landing', 
                               form_l=form_login, 
                               form_r=form_register)
    except:
        return redirect(url_for('error'))

@app.route("/logout")
def logout():
    """
        Route that logs a user out and sends them to the landing page
        Can be accessed anywhere on the site once a user has logged in
    """   
    try:
        logout_user()
        return redirect(url_for('landpage'))
    except:
        return redirect(url_for('error'))


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    """
        Page for users who are not logged on to request a password reset  
        Sends an email to the user with a link to a password reset page if they enter a valid email
    """   
    try:
        # Send user to the dashboard if they are logged in. This page is intended for those who forgot their password
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        form = RequestResetForm()

        # If the user has submitted the form with a valid email, send them an email with a link to the reset password page
        if form.validate_on_submit():
            user = User.get_user_by_email(form.email.data)
            send_reset_email(user)
            flash('An email has been sent with instructions for resetting your password!', 'info')
            return redirect(url_for('landpage'))
        close_session()
        return render_template('reset_request.html', 
                               title='Rest Password', 
                               form=form)
    except:
        return redirect(url_for('error'))
        
@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    """
        Page for users to reset their password
        Will not work if the route does not contain a valid token 
        This page can only be reached via an email sent to the user
    """      
    try:
        # Send user to the dashboard if they are logged in. This page is intended for those who forgot their password
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        # Verify that the token is valid and has not expired
        user = User.verify_reset_token(token)
        if user is None:
            flash('That is an invalid or expired token!', 'warning')
            return redirect(url_for('landpage'))

        form = ResetPasswordForm()
        
        # If the form has been submitted and is valid, reset their paassword
        if form.validate_on_submit():
        
            # Hash the new password that the user has chosen
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
          
            # Reset the password. If it updates correctly, tell the user that their password was updated
            if User.reset_pwd(user.id, hashed_password) == True:
                flash('Your password has been updated! You may now log in using it.', 'success')
                return redirect(url_for('landpage'))
            # If the password didn't update correctly, tell the user that it failed
            else:
                flash('Sorry, we were unable to update your password!', 'danger')
                return redirect(url_for('landpage'))
        close_session()
        return render_template('reset_token.html', 
                               title='Rest Password', 
                               form=form)
    except:
        return redirect(url_for('error'))

@app.route("/forgot_username", methods=['GET', 'POST'])
def forgot_username():
    """
        Page for users to request a reminder of their username
        Usernames are generated at registration and are unchangeable
        Sends an email to a user with their username if they enter a valid email
    """     
    try:
        # Send user to the dashboard if they are logged in. This page is intended for those who forgot their username
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        form = RequestResetUserForm()
        
        # If the form has been submitted and is valid, send the user an email with their username
        if form.validate_on_submit():
            user = User.get_user_by_email(form.email.data)
            send_forgot_username(user)
            flash('An email has been sent with your username attached!', 'info')
            return redirect(url_for('landpage'))
        close_session()
        return render_template('forgot_username.html', 
                               title='Rest User', 
                               form=form)
    except:
        return redirect(url_for('error'))    

@app.errorhandler(429)
def too_many_request(e):
    close_session()
    return render_template('login_limit.html')

@app.route("/term_of_service", methods=['GET'])
def term_of_service():
    close_session()
    return render_template('term_of_service.html')

@app.route("/error", methods=['GET'])
def error():
    close_session()
    return render_template('error.html')        
      
        
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                            User Routes
                These routes are used by the users of the game
    Typically, these routes involve the various features of the game
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
        
@app.route("/dashboard", methods=['GET', 'POST'])
@login_required
def dashboard():
    """
        Page that displays summary information about a student's progress
        This is the default page a user is taken to when they log in
    """   
    try:
        # Send admins to the admin page
        if (User.verify_role(current_user.id)):
            return redirect(url_for('admin'))
    
        # Using bcrypt to check the users role for some reason changes the SQLalchemy relationship loading to "lazy" instead of "subquery"
        # Reloading the user fixes this
        login_manager.current_user = User.get_user_by_username(current_user.username)
        
        # Get all the badges
        badges = Badge.get_all_badges()
       
        # Get Badge Progress and max points
        all_progress = {}  
        all_max_points = {}       
        for badge in badges:
            progress = User.get_badge_progress(current_user.id, badge.badge_id)
            all_progress[badge.badge_id] = progress
            max_points = Stamp.get_max_points(badge.badge_id)
            all_max_points[badge.badge_id] = max_points
            
        # Call the google api and pull all upcoming events
        events = get_event_list()
        
        # Parse the events into incoming and special groups
        mesa_days = searchEvents(events, ['Mesa','Day'])
        demo_days = searchEvents(events, ['Demo','Day'])
        future_events = [event for event in events if event['remain_days'] < 15]
        upcoming_events = [event for event in events if event['remain_days'] < 8]
        current_events = [event for event in events if event['remain_days'] < 3]
        mesa_events = get_mesa_events(future_events)

        close_session()
        return render_template('dashboard.html',
                               badges=badges,
                               progress=all_progress,
                               all_max_points=all_max_points,
                               events=events,
                               number_current=len(current_events),
                               upcoming_events=upcoming_events,
                               current_events=current_events,
                               mesa_days=mesa_days,
                               mesa_events=mesa_events,
                               demo_days=demo_days)
    except:
        return redirect(url_for('error'))

@app.route("/events", methods=['GET', 'POST'])
# @login_required
def events():
    """
        Page that displays summary information about a student's progress
        This is the default page a user is taken to when they log in
    """   
    try:
        # Send admins to the admin page
        if (User.verify_role(current_user.id)):
            return redirect(url_for('admin'))

        # Using bcrypt to check the users role for some reason changes the SQLalchemy relationship loading to "lazy" instead of "subquery"
        # Reloading the user fixes this
        login_manager.current_user = User.get_user_by_username(current_user.username)

        # Get all the badges
        badges = Badge.get_all_badges()
        #badge_names, badge_ids = [row.badge_name for row in badges], [row.badge_id for row in badges]

        # Get Badge Progress
        all_progress = {}    
        for badge in badges:
            progress = User.get_badge_progress(current_user.id, badge.badge_id)
            all_progress[badge.badge_id] = progress
            
        # Call the google api and pull all upcoming events
        events = get_event_list()

        # Parse the events into incoming and special groups
        mesa_days = searchEvents(events, ['Mesa','Day'])
        demo_days = searchEvents(events, ['Demo','Day'])
        future_events = [event for event in events if event['remain_days'] < 15]
        upcoming_events = [event for event in events if event['remain_days'] < 8]
        current_events = [event for event in events if event['remain_days'] < 3]
        mesa_events = get_mesa_events(future_events)
        close_session()
        return render_template('events.html',
                               badges=badges,
                               progress=all_progress,
                               events=events,
                               number_current=len(current_events),
                               upcoming_events=upcoming_events,
                               current_events=current_events,
                               mesa_days=mesa_days,
                               mesa_events=mesa_events,
                               demo_days=demo_days)
    except:
        return redirect(url_for('error'))
   
@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    """
        Page for users to change their account information
        Page is broken up into separate forms for each section, so they can only update their account one piece at a time
    """    
    try:
        # Send admins to the admin page
        if (User.verify_role(current_user.id)):
            return redirect(url_for('admin'))

        # Using bcrypt to check the users role for some reason changes the SQLalchemy relationship loading to "lazy" instead of "subquery"
        # Reloading the user fixes this
        login_manager.current_user = User.get_user_by_username(current_user.username)

        emailform = UpdateEmailForm()
        nameform = UpdateNameForm()
        schoolform = UpdateSchoolForm()
        passwordform= UpdatePasswordForm()
        avatars = ""
        myaccount = User.get_user_by_username(current_user.username)

        #Get all badges
        badges = Badge.get_all_badges()

        #Update password
        if passwordform.password.data and passwordform.validate_on_submit():
            hashed_password = bcrypt.generate_password_hash(passwordform.password.data).decode('utf-8')
            if User.reset_pwd(myaccount.id, hashed_password) == True:
                flash('Your account has been successfully updated!', 'success')
            else:
                flash('Sorry, we were unable to update your account!', 'danger')
            return redirect(url_for('account'))

        #Update email
        if emailform.email.data and emailform.validate_on_submit():
            if User.update_email(myaccount.id, emailform.email.data) == True:
                flash('Your account has been successfully updated!', 'success')
            else:
                flash('Sorry, we were unable to update your account!', 'danger')
            return redirect(url_for('account'))

        #Update name
        if (nameform.firstname.data or nameform.lastname.data) and nameform.validate_on_submit():
            if User.update_name(myaccount.id, nameform.firstname.data, nameform.lastname.data) == True:
                flash('Your account has been successfully updated!', 'success')
            else:
                flash('Sorry, we were unable to update your account!', 'danger')
            return redirect(url_for('account'))

        #Update school
        if schoolform.school.data and schoolform.validate_on_submit():
            if User.update_school(myaccount.id, schoolform.school.data) == True:
                flash('Your account has been successfully updated!', 'success')
            else:
                flash('Sorry, we were unable to update your account!', 'danger')
            return redirect(url_for('account'))

        if request.method=='POST':

            #Update avatar
            avatarSelect = request.form.get('avatarSelect')
            if avatarSelect:
                if User.update_avatar(myaccount.id, avatarSelect) == True:
                    flash('Your account has been successfully updated!', 'success')
                else:
                    flash('Sorry, we were unable to update your account!', 'danger')
                return redirect(url_for('account'))

        # Get all the badges
        badges = Badge.get_all_badges_id_with_names()

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
        demo_days = searchEvents(events, ['Demo','Day'])
        future_events = [event for event in events if event['remain_days'] < 15]
        upcoming_events = [event for event in events if event['remain_days'] < 8]
        current_events = [event for event in events if event['remain_days'] < 3]
        mesa_events = get_mesa_events(future_events)
        close_session()
        return render_template('account.html', 
                                title='Account', 
                                badges=badges,
                                avatar_files=Avatar.get_all_avatars(), 
                                form_email=emailform, 
                                form_name=nameform, 
                                form_password=passwordform, 
                                form_school=schoolform, 
                                events=events, 
                                number_current=len(current_events), 
                                current_events=current_events, 
                                upcoming_events=upcoming_events, 
                                mesa_days=mesa_days,
                                mesa_events=mesa_events,
                                demo_days=demo_days)
        
    except:    
        return redirect(url_for('error'))    

@app.route("/account_deactivate", methods=['GET', 'POST'])
@login_required
def account_deactivate():

    try:
        # Send admins to the admin page
        if (User.verify_role(current_user.id)):
            return redirect(url_for('admin'))

        # Using bcrypt to check the users role for some reason changes the SQLalchemy relationship loading to "lazy" instead of "subquery"
        # Reloading the user fixes this
        login_manager.current_user = User.get_user_by_username(current_user.username)

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
                    flash('Account information does not match. Please check your first and last name!', 'danger')
            return redirect(url_for('account'))

    except:
        return redirect(url_for('error')) 

@app.route("/earn_stamps", methods=['GET', 'POST'])
@login_required
def earn_stamps():
    """
        Page for users earn stamps
        Users pick a stamp and enter they date they accomplished the task
        The stamp will be added to the user's account and does not do any verification
            as to whether or not they actually did the task
    """  
    try:
        # Send admins to the admin page
        if (User.verify_role(current_user.id)):
            return redirect(url_for('admin'))

        # Using bcrypt to check the users role for some reason changes the SQLalchemy relationship loading to "lazy" instead of "subquery"
        # Reloading the user fixes this
        login_manager.current_user = User.get_user_by_username(current_user.username)

        # Get all badge names
        badge_names = [row.badge_name for row in Badge.get_all_badges_names()]   

        # A dictionary that maps badge_ids to badge_name
        badges = {row.badge_id : row.badge_name for row in Badge.get_all_badges_id_with_names()}.items()    
        
        forms, t = [], 1       # several pairs of forms (stamp, date, submit). t is used to assign unique id
        for badge in badges:
            stamps = Stamp.get_user_stamps_of_badge(current_user.id, badge[0])

            if stamps is not None:
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
        badges = Badge.get_all_badges()

        # Call the google api and pull all upcoming events
        events = get_event_list()
        
        # Parse the events into incoming and special groups
        mesa_days = searchEvents(events, ['Mesa','Day'])
        demo_days = searchEvents(events, ['Demo','Day'])
        future_events = [event for event in events if event['remain_days'] < 15]
        upcoming_events = [event for event in events if event['remain_days'] < 8]
        current_events = [event for event in events if event['remain_days'] < 3]
        mesa_events = get_mesa_events(future_events)
        close_session()
        return render_template('earnstamps.html', 
                                title='Earn Stamps', 
                                forms=forms, 
                                badges=badges, 
                                events=events,
                                number_current=len(current_events), 
                                current_events=current_events, 
                                upcoming_events=upcoming_events, 
                                mesa_days=mesa_days,
                                mesa_events=mesa_events,
                                demo_days=demo_days)
    except:
        return redirect(url_for('error')) 
        
@app.route("/badges<badge_id>", methods=['GET', 'POST'])
@login_required
def check_badge(badge_id):
    """
        Page for checking a user's progress on an individual badge
        The particular badge being view is passed in through the route
    """  
    try:
        # Send admins to the admin page
        if (User.verify_role(current_user.id)):
            return redirect(url_for('admin'))

        # Using bcrypt to check the users role for some reason changes the SQLalchemy relationship loading to "lazy" instead of "subquery"
        # Reloading the user fixes this
        login_manager.current_user = User.get_user_by_username(current_user.username)

        # Get all the badges
        badges = Badge.get_all_badges()

        # Get the current badge being viewed
        badge = Badge.get_badge_by_id(badge_id)
          
        # Get the id of current user and separate the stamps that they have earned from the one's they have not earned
        user_id = current_user.id    
        unearned_stamps = [row.stamp_name for row in Stamp.get_unearned_stamps_of_badge(user_id, badge.badge_id)]     
        earned_stamps = [row for row in UserStamp.get_earned_stamps_of_badge(user_id, badge.badge_id)]
        
        # If all the stamps for this badge have been earned, print this instead
        if not unearned_stamps:
            unearned_stamps = ['All stamps earned'] 
        
        # Get the user's progress on the badge
        badge_progress = User.get_badge_progress(user_id, badge.badge_id)
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
            return redirect('/badges' + str(badge_id))
        
        # Call the google api and pull all upcoming events
        events = get_event_list()
        
        # Parse the events into incoming and special groups
        mesa_days = searchEvents(events, ['Mesa','Day'])
        demo_days = searchEvents(events, ['Demo','Day'])
        future_events = [event for event in events if event['remain_days'] < 15]
        upcoming_events = [event for event in events if event['remain_days'] < 8]
        current_events = [event for event in events if event['remain_days'] < 3]
        mesa_events = get_mesa_events(future_events)
        close_session()
        return render_template('badges.html', 
                                badges=badges,
                                badge=badge, 
                                unearned=unearned_stamps, 
                                earned=earned_stamps, 
                                pt=points, 
                                lv=current_level, 
                                to_next_lv=to_next_lv, 
                                events=events,
                                number_upcoming=len(upcoming_events),
                                upcoming_events=upcoming_events, 
                                number_current=len(current_events),
                                current_events=current_events,
                                mesa_days=mesa_days, 
                                demo_days=demo_days, 
                                mesa_events=mesa_events)
    except:
        return redirect(url_for('error')) 


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                            Admin Routes
                These routes are used by the admins
    Typically, these routes involve ways to change the rules/settings
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

# Added by Millen
# Load admin page if role is admin
@app.route("/admin")
@login_required
def admin():
    '''
    Default landing page for admins.
    Page displays the top three scores for each badge, and which users have those top 3 scores
    '''
    try:
        # https://stackoverflow.com/questions/21895839/restricting-access-to-certain-areas-of-a-flask-view-function-by-role
        if not User.verify_role(current_user.id):
            return redirect(url_for('dashboard'))

        # Using bcrypt to check the users role for some reason changes the SQLalchemy relationship loading to "lazy" instead of "subquery"
        # Reloading the user fixes this
        login_manager.current_user = User.get_user_by_username(current_user.username)

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
            
            if top_badge_scores:
                # For each top score, get all the users that have that score        
                for top_score in top_badge_scores:
                    # Add each user with a top score to and array of users/top scores
                    users_with_top_score = User.get_record_holders(badge.badge_id, top_score.total_points)
                    for user in users_with_top_score:
                        record_holders.append(user)
            # Add the array of users/top scores to the total list of scores (indexed by the badge id)
            top_scores[badge.badge_id] = record_holders
        
        # Call the google api and pull all upcoming events
        events = get_event_list()
        
        # Parse the events into incoming and special groups
        mesa_days = searchEvents(events, ['Mesa','Day'])
        demo_days = searchEvents(events, ['Demo','Day'])
        future_events = [event for event in events if event['remain_days'] < 15]
        upcoming_events = [event for event in events if event['remain_days'] < 8]
        current_events = [event for event in events if event['remain_days'] < 3]
        mesa_events = get_mesa_events(future_events)
        close_session()
        return render_template('admin.html', badges=badges, top_scores=top_scores, events=events,
                                    number_upcoming=len(upcoming_events),
                                    upcoming_events=upcoming_events, 
                                    number_current=len(current_events),
                                    current_events=current_events,
                                    mesa_days=mesa_days, 
                                    demo_days=demo_days, 
                                    mesa_events=mesa_events)
    except:
        return redirect(url_for('error')) 

@app.route("/admin_control", methods=['GET', 'POST'])
@login_required    
def admin_control():
    """
        Page for admin to control various parts of the application
        Admins can add or remove schools, remove old accounts, set academic year, and manage the admin account
        Only those will a valid admin account can view this page
    """ 
    try:    
        if not User.verify_role(current_user.id):
            return redirect(url_for('dashboard'))

        # Using bcrypt to check the users role for some reason changes the SQLalchemy relationship loading to "lazy" instead of "subquery"
        # Reloading the user fixes this
        login_manager.current_user = User.get_user_by_username(current_user.username)

        emailform = UpdateEmailForm()
        passwordform = UpdatePasswordForm()
        oldaccountsform = RemoveOldAccountsForm()
        resetdateform = ResetDateForm()
        addschoolform = AddSchoolForm()
        deleteschoolform =DeleteSchoolForm()
        resetdateform.reset_date.id = 'reset_date'
        admin_account = User.get_user_by_username(current_user.username)

        #Add School
        if addschoolform.schoolName.data and addschoolform.validate_on_submit():
            schoolName = request.form.get('schoolName')
            # Add school to the database
            new_school = School(schoolName, '', '', '', '')
            School.add_new_school(new_school)
            rows = School.get_school()
            flash('New school option has been added!', 'success')
            return redirect(url_for('admin_control'))

        #Delete School Form
        if deleteschoolform.school.data and deleteschoolform.validate_on_submit():
            school_id = deleteschoolform.school.data
            School.delete_school_by_id(school_id)
            flash('Successfully  deleted school!', 'success')
            return redirect(url_for('admin_control'))

        #Update password
        if passwordform.password.data and passwordform.validate_on_submit():
            hashed_password = bcrypt.generate_password_hash(passwordform.password.data).decode('utf-8')
            if User.reset_pwd(admin_account.id, hashed_password) == True:
                flash('Your account has been successfully updated!', 'success')
            else:
                flash('Sorry, we were unable to update your account!', 'danger')
            return redirect(url_for('admin_control'))

        #Update email
        if emailform.email.data and emailform.validate_on_submit():
            if User.update_email(admin_account.id, emailform.email.data) == True:
                flash('Your account has been successfully updated!', 'success')
            else:
                flash('Sorry, we were unable to update your account!', 'danger')
            return redirect(url_for('admin_control'))
            
        #Remove old accounts
        if oldaccountsform.years.data and oldaccountsform.validate_on_submit():   
            results = User.delete_innactive_accounts(oldaccountsform.years.data)
            if results:
                flash('Successfully removed ' + str(results) + ' account(s)!', 'success')
            else:
                flash('No accounts were deleted!', 'success')
            return redirect(url_for('admin_control'))
            
        #Change reset date    
        if resetdateform.reset_date.data and resetdateform.validate_on_submit():
            if Reset_Date.change_date(resetdateform.reset_date.data):
                flash('Successfully changed the reset date to ' +  str(resetdateform.reset_date.data)[5:] + '!', 'success')
            else:
                flash('Sorry, we were not able to change the date!', 'danger')
            return redirect(url_for('admin_control'))
            

        #Load page
        resetdateform.reset_date.data = Reset_Date.get_reset_date().reset_date
        emailform.email.data = current_user.email

        # Call the google api and pull all upcoming events
        events = get_event_list()
        
        # Parse the events into incoming and special groups
        mesa_days = searchEvents(events, ['Mesa','Day'])
        demo_days = searchEvents(events, ['Demo','Day'])
        future_events = [event for event in events if event['remain_days'] < 15]
        upcoming_events = [event for event in events if event['remain_days'] < 8]
        current_events = [event for event in events if event['remain_days'] < 3]
        mesa_events = get_mesa_events(future_events)
        close_session()
        return render_template('admin_control.html', form_email=emailform, form_password=passwordform, form_old_accounts=oldaccountsform, form_reset_date=resetdateform,form_school_add=addschoolform,form_school_delete=deleteschoolform, events=events,
                                    number_upcoming=len(upcoming_events),
                                    upcoming_events=upcoming_events, 
                                    number_current=len(current_events),
                                    current_events=current_events,
                                    mesa_days=mesa_days, 
                                    demo_days=demo_days, 
                                    mesa_events=mesa_events)

    except:
        return redirect(url_for('error')) 

@app.route("/admin_settings", methods=['GET', 'POST'])
@login_required
def admin_settings():
    '''
    Route for the admin settings page
    On this page, an admin can change required badge points, add stamps, remove stamps, change badge name, or change badge icon
    '''
    try: 
        if not User.verify_role(current_user.id):     
            return redirect(url_for('dashboard'))

        # Using bcrypt to check the users role for some reason changes the SQLalchemy relationship loading to "lazy" instead of "subquery"
        # Reloading the user fixes this
        login_manager.current_user = User.get_user_by_username(current_user.username)

        badges = Badge.get_all_badges()
        badge_forms = {}
        addstampform = AddStampForm()
        deletestampform = DeleteStampForm()        
        badgenameform = EditBadgeForm()

        # Changing badge score 
        for badge in badges:
            form = BadgePointsForm(prefix=str(badge.badge_id)) 
            if form.submit.data and form.validate_on_submit():
                if Badge.change_points(badge.badge_id, form.level1_points.data, form.level2_points.data, form.level3_points.data, form.level4_points.data, \
                        form.level5_points.data, form.level6_points.data, form.level7_points.data, form.level8_points.data, form.level9_points.data, form.level10_points.data):
                    flash('Successfully changed badge points!', 'success')
                else:
                    flash('Sorry, we were not able to change the badge points!', 'danger')
                return redirect(url_for('admin_settings'))        
            form.level1_points.data = badge.level1_points    
            form.level2_points.data = badge.level2_points            
            form.level3_points.data = badge.level3_points           
            form.level4_points.data = badge.level4_points            
            form.level5_points.data = badge.level5_points          
            form.level6_points.data = badge.level6_points            
            form.level7_points.data = badge.level7_points            
            form.level8_points.data = badge.level8_points           
            form.level9_points.data = badge.level9_points           
            form.level10_points.data = badge.level10_points                    
            badge_forms[badge.badge_id] = form 

        # Adding New Stamp
        if addstampform.badge.data and addstampform.validate_on_submit():
            newStamp=Stamp(addstampform.stamp_name.data,addstampform.badge.data,addstampform.points.data,None)
            Stamp.add_stamp(newStamp)
            flash('New stamp has been created!', 'success')
            return redirect(url_for('admin_settings'))


        # Deleting a Stamp
        if deletestampform.submitdelete.data and deletestampform.validate_on_submit():  
            stampName=Stamp.get_stamp_by_stamp_id(deletestampform.stampdelete.data)
            Stamp.delete_stamp_by_id(deletestampform.stampdelete.data)
            flash('Stamp deleted successfully!', 'success')
            return redirect(url_for('admin_settings'))

        # Updating a Badge Name
        if badgenameform.badgeName.data and badgenameform.validate_on_submit():
            badgeId=badgenameform.badge.data
            badgeName= badgenameform.badgeName.data
            Badge.update_badge_name(badgeId,badgeName)
            flash('Badge name has been successfully updated!', 'success')
            return redirect(url_for('admin_settings'))


        #Update Icon
        if request.method=='POST':
            iconSelect = request.form.get('iconSelect')
            if iconSelect:
                badgeSelect = request.form.get('iconBadgeSelect')

                if Badge.update_icon(badgeSelect, iconSelect) == True:
                    flash('Badge icon has been successfully updated!', 'success')
                else:
                    flash('Sorry, we were unable to update the badge icon!', 'danger')
                return redirect(url_for('admin_settings'))

        deletestampform.stampdelete.choices = Stamp.get_stamps_of_badge(1)

        # Call the google api and pull all upcoming events
        events = get_event_list()
        
        # Parse the events into incoming and special groups
        mesa_days = searchEvents(events, ['Mesa','Day'])
        demo_days = searchEvents(events, ['Demo','Day'])
        future_events = [event for event in events if event['remain_days'] < 15]
        upcoming_events = [event for event in events if event['remain_days'] < 8]
        current_events = [event for event in events if event['remain_days'] < 3]
        mesa_events = get_mesa_events(future_events)
        close_session()
        return render_template('admin_settings.html', badge_forms=badge_forms, form_add_stamp=addstampform, form_delete_stamp=deletestampform, \
                form_badge_name=badgenameform, badges=badges, icon_files=Icon.get_all_icons(), events=events,
                                number_upcoming=len(upcoming_events),
                                upcoming_events=upcoming_events, 
                                number_current=len(current_events),
                                current_events=current_events,
                                mesa_days=mesa_days, 
                                demo_days=demo_days, 
                                mesa_events=mesa_events)
    except:
        return redirect(url_for('error')) 

@app.route('/stamp/<badgeid>')
def stamp(badgeid):
    '''
        This route dynamically returns all the stamps for a badge as a json
        Used by the admin settings
    '''
    stamps = Stamp.get_stamps_of_badge(badgeid)
    stampArray = []
    for stamp in stamps:
        stampObj = {}
        stampObj['id'] = stamp.stamp_id
        stampObj['name'] = stamp.stamp_name
        stampArray.append(stampObj)

    return jsonify({'stamps' : stampArray})

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                        Route Functions
       Supporting functions used throughout the various routes
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
 
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


