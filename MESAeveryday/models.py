"""
This file contains all tables in the database. It uses SQLAlchemy to map the tables to python objects
All queries and session management is done in this file
All classes here are based on a table in the database. If a change is made to the database, those changes must be reflected here as well

Modified from CoreyMSchafer's Flask Tutorial
https://github.com/CoreyMSchafer/code_snippets/blob/master/Python/Flask_Blog/06-Login-Auth/flaskblog/routes.py
"""
import datetime
from dateutil.relativedelta import relativedelta
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from MESAeveryday import login_manager, app, bcrypt
from flask_login import UserMixin
from flask import flash
import os
from sqlalchemy import Column, Integer, String, create_engine, ForeignKey, DateTime, Date, or_, and_, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref

# db_connection uses mysql+pymysql as otherwise certain libraries that are not supported by python3 will need to be installed
# Check link to it here: https://stackoverflow.com/questions/22252397/importerror-no-module-named-mysqldb

#db_connection uses mysql+pymysql as otherwise certain libraries that are not supported by python3 will need to be installed
#check link to it here: https://stackoverflow.com/questions/22252397/importerror-no-module-named-mysqldb
# db_connection = 'mysql+pymysql://' + os.environ['MESAusername'] + ':' + os.environ['MESApassword'] + '@' + os.environ['MESAhostname'] + ':3306/' + os.environ['MESAusername']
db_connection = 'mysql+pymysql://' + os.environ['MESAusername'] + ':' + os.environ['MESApassword'] + '@' + os.environ['MESAhostname'] + ':3306/' + os.environ['MESAusername']
# Create a session with the database
engine = create_engine(db_connection, pool_recycle=3600)
Base = declarative_base(engine)
metadata = Base.metadata
Session = sessionmaker(bind=engine)
session = Session()

@login_manager.user_loader
def load_user(user_id):
    """
        Function used to load a user
        Used by the login manager to obtain the information of a user who is logged in  
    """
    try:
        return session.query(User).filter(User.id==user_id).first()
    except:
        session.rollback()
        return None

def close_session():
    session.close()

#All classes here are based on a table in the database. If a change is made to the database, those changes must be reflected here as well

#Class for the "users" table
class User(Base, UserMixin):

    __tablename__ = 'users'

    id = Column('user_id', Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String)
    email = Column(String)
    role = Column(String)
    school_id = Column(Integer, ForeignKey("schools.school_id"))
    avatar_id = Column(Integer, ForeignKey("avatars.id"))
    password = Column('SSB', String)
    last_login = Column(DateTime)

    school = relationship("School", foreign_keys=[school_id], lazy='subquery')
    avatar = relationship("Avatar", foreign_keys=[avatar_id], lazy='subquery')

    def __init__(self, username, first_name, last_name, email, password, school_id):
        self.username = username
        self.email = email
        self.avatar_id = 1
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.school_id = school_id
        self.role = 'user'

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
            return session.query(User).filter(User.id==user_id).first()
        except:
            session.rollback()
            return None
   
    def get_all_username():
        try:
            return session.query(User.username)
        except:
            session.rollback()
            return None

    def validate_username(username):
        try:
            user = session.query(User).filter(User.username == username.data).first()
        except:
            session.rollback()
            user = None
        if user:
            return True
        else:
            return False

    def validate_email(email):
        try:
            user = session.query(User).filter(User.email == email.data).first()
        except:
            session.rollback()
            user = None
        if user:
            return True
        else:
            return False

    def add_new_user(new_user):
        try:
            session.add(new_user)
            session.commit()
        except:
            session.rollback()

    def get_user_by_email(email):
        try:
            return session.query(User).filter(User.email == email).first()
        except:
            session.rollback()
            return None

    def get_user_by_username(username):
        try:
            return session.query(User).filter(User.username == username).first()
        except:
            session.rollback()
            return None
    def delete_user_by_id(id):
        try:
            session.query(User).filter(User.id == id).delete()
            session.commit()
        except:
            session.rollback()
            return None

    def reset_pwd(id, hashed_pwd):
      
        try:
            row = session.query(User).filter(User.id == id).first()
            row.password = hashed_pwd
            session.commit()
        except:
            session.rollback()
            return False
        return True

    def update_last_login(id, new_last_login):
        try:
            row = session.query(User).filter(User.id == id).first()
            row.last_login = new_last_login
            session.commit()
        except:
            session.rollback()
            return False
        return True

    def update_name(id, new_first_name, new_last_name):
        try:
            row = session.query(User).filter(User.id == id).first()
            row.first_name = new_first_name
            row.last_name = new_last_name
            session.commit()
        except:
            session.rollback()
            return False
        return True

    def update_email(id, new_email):
        try:
            row = session.query(User).filter(User.id == id).first()
            row.email = new_email
            session.commit()
        except:
            session.rollback()
            return False
        return True

    def update_school(id, new_school_id):
        try:
            row = session.query(User).filter(User.id == id).first()
            row.school_id = new_school_id
            session.commit()
        except:
            session.rollback()
            return False
        return True

    def update_avatar(id, new_avatar_id):
        try:
            row = session.query(User).filter(User.id == id).first()
            row.avatar_id = new_avatar_id
            session.commit()
        except:
            session.rollback()
            return False
        return True 
    
    def get_badge_progress(user_id, badge_id):
        try:
            return session.execute("SELECT total_points, current_level, to_next_level FROM user_aggregate WHERE user_id = :user_id AND badge_id = :badge_id", {'user_id':user_id, 'badge_id':badge_id}).first()
        except:
            session.rollback()
            return None
        
    def get_record_holders(badge_id, top_score):
        try:
            return session.execute("SELECT u.first_name, u.last_name, s.school_name, ug.total_points, ug.current_level FROM user_aggregate ug JOIN users u ON ug.user_id = u.user_id JOIN schools s ON u.school_id = s.school_id WHERE ug.badge_id = :badge_id AND ug.total_points = :top_score", {'badge_id':badge_id, 'top_score':top_score})
        except:
            session.rollback()
            return None

    def get_users_by_school(school_id):
        try: 
            return session.query(User).filter(User.school_id == school_id)
        except:
            session.rollback()
            return None

    # Added by Millen
    # Checks if user had an admin role
    def verify_role(id):
        try:
            target = session.query(User).filter(User.id == id).first()
            if(target.role == "admin"):
                return True
            else:
                return False
        except:
            session.rollback()
            return False
            
    def delete_innactive_accounts(years_innactive):
        try:            
            results = session.query(User).filter(and_(User.last_login < datetime.datetime.now() - relativedelta(years=years_innactive)), (User.last_login != None)).delete()
            session.commit()
            return results
        except:
            session.rollback()
            return None
            
#Class for the "schools" table
class School(Base):
    __tablename__ = 'schools'

    school_id = Column(Integer, primary_key=True)
    school_name = Column(String)
    district = Column(String)
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)

    def __init__(self, school_name, district, city, state, zip_code):
	    self.school_name = school_name
	    self.district = district
	    self.city = city
	    self.state = state
	    self.zip_code = zip_code

    def get_all_schools_names():
        try:
            # The union ensures that the "Other" will always be found at the end
            results = session.query(School.school_id, School.school_name).filter(School.school_name != 'Other').order_by(School.school_name.asc())\
                .union(session.query(School.school_id, School.school_name).filter(School.school_name == 'Other'))
            return results
        except:
            session.rollback()
            return None
    def get_school():
        try:
            results=session.query(School.school_name).all()
            return results
        except:
            session.rollback()
            return None

    def add_new_school(new_school):
        try:
            session.add(new_school)
            session.commit()
        except:
            session.rollback()

    def delete_school_by_id(id):
        try:
            other_school = School.get_school_by_name('Other')
            users = User.get_users_by_school(id)
            for user in users:
                user.school_id = other_school.school_id
            session.query(School).filter(School.school_id == id).delete()
            session.commit()
        except:
            session.rollback()
            return None
    def get_school_by_id(id):
        try:
           return session.query(School.school_name).filter(School.school_id == id).first()

        except:
            session.rollback()
            return None
    def get_school_by_name(name):
        try:
           return session.query(School).filter(School.school_name == name).first()

        except:
            session.rollback()
            return None


#Class for the "badges" table
class Badge(Base):
    __tablename__ = 'badges'

    badge_id = Column(Integer, primary_key=True)
    badge_name = Column(String)
    color = Column(String)
    icon_id = Column(Integer, ForeignKey("badge_icons.id"))

    level1_points = Column(Integer)
    level2_points = Column(Integer)
    level3_points = Column(Integer)
    level4_points = Column(Integer)
    level5_points = Column(Integer)
    level6_points = Column(Integer)
    level7_points = Column(Integer)
    level8_points = Column(Integer)
    level9_points = Column(Integer)
    level10_points = Column(Integer)
    
    icon = relationship("Icon", foreign_keys=[icon_id], lazy='subquery')

    def __init__(self, badge_name, color, level1_points, level2_points, level3_points, level4_points,
                    level5_points, level6_points, level7_points, level8_points, level9_points, level10_points):
        self.badge_name = badge_name
        self.level1_points = level1_points
        self.level2_points = level2_points
        self.level3_points = level3_points
        self.level4_points = level4_points
        self.level5_points = level5_points
        self.level6_points = level6_points
        self.level7_points = level7_points
        self.level8_points = level8_points
        self.level9_points = level9_points
        self.level10_points = level10_points

        
    def get_all_badges():
        try:
            return session.query(Badge)
        except:
            session.rollback()
            return None          
            
    def get_badge_by_id(badge_id):
        try:
            return session.query(Badge).filter(Badge.badge_id == badge_id).first()
        except:
            session.rollback()
            return None   
        
    def get_all_badges_names():
        try:
            return session.query(Badge.badge_name)
        except:
            session.rollback()
            return None

    def get_all_badges_id_with_names():
        try:
            return session.query(Badge.badge_id, Badge.badge_name)
        except:
            session.rollback()
            return None
                     
    def get_badge_name(badge_id):
        try:
            return session.query(Badge.badge_name).filter(Badge.badge_id == badge_id)
        except:
            session.rollback()
            return None

    def get_top_scores(badge_id):
        try:
            return session.execute("SELECT total_points FROM user_aggregate WHERE badge_id = :badge_id AND total_points != 0 GROUP BY total_points ORDER BY total_points DESC LIMIT 3", {'badge_id':badge_id})
        except:
            session.rollback()
            return None
           


    def update_badge_name(badge_id,new_badge_name):
        try:
           badge=session.query(Badge).filter(Badge.badge_id==badge_id).first()
           badge.badge_name=new_badge_name
           session.commit()

        except:
            session.rollback()
            return None

    def update_icon(id, new_icon_id):
        try:
            badge = session.query(Badge).filter(Badge.badge_id == id).first()
            badge.icon_id = new_icon_id
            session.commit()
            return True
        except:
            session.rollback()
            return False



            
    def change_points(badge_id, level1_points, level2_points, level3_points, level4_points, level5_points, level6_points, level7_points, level8_points, level9_points, level10_points):
        try: 
            badge = session.query(Badge).filter(Badge.badge_id == badge_id).first()        
            badge.level1_points = level1_points         
            badge.level2_points = level2_points            
            badge.level3_points = level3_points            
            badge.level4_points = level4_points
            badge.level5_points = level5_points
            badge.level6_points = level6_points
            badge.level7_points = level7_points
            badge.level8_points = level8_points
            badge.level9_points = level9_points
            badge.level10_points = level10_points
            session.commit()
            return True
        except:
            session.rollback()
            return False
            

#Class for the "stamps" table
class Stamp(Base, UserMixin):
    __tablename__ = 'stamps'

    stamp_id = Column(Integer, primary_key=True)
    stamp_name = Column(String)
    badge_id = Column(Integer, ForeignKey("badges.badge_id"))
    points = Column(Integer)
    url = Column(String)

    badge = relationship("Badge", foreign_keys=[badge_id], lazy='subquery')

    def __init__(self, stamp_name, badge_id, points, url):
        self.stamp_name = stamp_name
        self.badge_id = badge_id
        self.points = points
        self.url = url

    def get_user_stamps_of_badge(user_id, badge_id):
        try:
            reset_date = session.query(Reset_Date.reset_date).first().reset_date.strftime('%m-%d')
            if datetime.datetime.now().strftime('%m-%d') >= reset_date:
                last_reset_date = str(datetime.datetime.now().year) + '-' + str(reset_date)
            else:
                last_reset_date = str(datetime.datetime.now().year -1) + '-' + str(reset_date)
            subquery = session.query(UserStamp.stamp_id).filter(and_(UserStamp.user_id == user_id, UserStamp.log_date >= last_reset_date))
            return session.query(Stamp.stamp_id, Stamp.stamp_name).filter(Stamp.badge_id == badge_id).filter(Stamp.stamp_id.notin_(subquery))
        except:
            session.rollback()
            return None

    def get_all_stamps():
        try:
            return session.query(Stamp.stamp_id, Stamp.stamp_name)
        except:
            session.rollback()
            return None

    def get_stamps_of_badge(badge_id):
        try:
            return session.query(Stamp.stamp_id, Stamp.stamp_name).filter(Stamp.badge_id == badge_id)
        except:
            session.rollback()
            return None

    def get_unearned_stamps_of_badge(user_id, badge_id):
        try:
            reset_date = session.query(Reset_Date.reset_date).first().reset_date.strftime('%m-%d')
            if datetime.datetime.now().strftime('%m-%d') >= reset_date:
                last_reset_date = str(datetime.datetime.now().year) + '-' + str(reset_date)
            else:
                last_reset_date = str(datetime.datetime.now().year -1) + '-' + str(reset_date)
            subquery = session.query(UserStamp.stamp_id).filter(and_(UserStamp.user_id == user_id, UserStamp.log_date >= last_reset_date))
            return session.query(Stamp).filter(Stamp.badge_id == badge_id).filter(Stamp.stamp_id.notin_(subquery))
        except:
            session.rollback()
            return None


    def get_earned_stamps_of_badge(user_id, badge_id):
        try:
            subquery = session.query(UserStamp.stamp_id).filter(UserStamp.user_id == user_id)
            return session.query(Stamp).filter(Stamp.badge_id == badge_id).filter(Stamp.stamp_id.in_(subquery))
        except:
            session.rollback()
            return None

    def add_stamp(new_stamp):
        try:
            session.add(new_stamp)
            session.commit()
        except:
            session.rollback()
            return None
    def get_all_stampid_stampname():
        try:
            return session.query(Stamp.stamp_id, Stamp.stamp_name).all()
        except:
            session.rollback()
            return None

    def get_stamp_by_stamp_id(stamp_id):
        try:
            return session.query(Stamp.stamp_name).filter(Stamp.stamp_id == stamp_id).first()
        except:
            session.rollback()
            return None

    def get_stamp_by_name(name):
        try:
            return session.query(Stamp).filter(Stamp.stamp_name == name).first()
        except:
            session.rollback()
            return None

    def delete_stamp_by_id(id):
        try:
            session.query(Stamp).filter(Stamp.stamp_id == id).delete()
            session.commit()
        except:
            session.rollback()
            return None


            
    def get_max_points(badge_id):
        try:
            return session.query(func.sum(Stamp.points).label('max_points')).filter(Stamp.badge_id == badge_id).first()
        except:
            session.rollback()
            return None
            
    


#Class for the "user_stamps" table
class UserStamp(Base, UserMixin):
    __tablename__ = 'user_stamps'

    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    stamp_id = Column(Integer, ForeignKey("stamps.stamp_id"), primary_key=True)
    log_date = Column(DateTime, primary_key=True)
    stamp_date = Column(Date)

    user = relationship("User", foreign_keys=[user_id], lazy='subquery')
    stamp = relationship("Stamp", foreign_keys=[stamp_id], lazy='subquery')

    def __init__(self, user_id, stamp_id, log_date, stamp_date):
        self.user_id = user_id
        self.stamp_id = stamp_id
        self.log_date = log_date
        self.stamp_date = stamp_date

    def earn_stamp(user_id, stamp_id, log_date, stamp_date):
        new_UserStamp = UserStamp(user_id, stamp_id, log_date, stamp_date)
        try:
            session.add(new_UserStamp)
            session.commit()
        except:
            session.rollback()
            return False
        return True



    def get_earned_stamps_of_badge(user_id, badge_id):
        try:
            reset_date = session.query(Reset_Date.reset_date).first().reset_date.strftime('%m-%d')
            if datetime.datetime.now().strftime('%m-%d') >= reset_date:
                last_reset_date = str(datetime.datetime.now().year) + '-' + str(reset_date)
            else:
                last_reset_date = str(datetime.datetime.now().year -1) + '-' + str(reset_date)
            return session.query(UserStamp.stamp_id, UserStamp.log_date, UserStamp.stamp_date, Stamp.stamp_name).filter(and_(and_(and_(UserStamp.user_id == user_id, Stamp.stamp_id == UserStamp.stamp_id), UserStamp.log_date >= last_reset_date), Stamp.badge_id == badge_id))
        except:
            session.rollback()
            return None

    def delete_stamp(user_id, stamp_id, stamp_date, log_date):
        try:
            # Query = UserStamp.query.filter_by(user_id == user_id, stamp_id == stamp_id, stamp_date == stamp_date, log_date == log_date).first()
            Query = session.query(UserStamp).filter(UserStamp.user_id == user_id).filter(UserStamp.stamp_id == stamp_id).filter(UserStamp.stamp_date == stamp_date).filter(UserStamp.log_date == log_date).first()
            if not Query:
                return False
            session.delete(Query)
            session.commit()
        except:
            session.rollback()
            return False
        return True

#Class for the "avatars" table
class Avatar(Base):
    __tablename__ = 'avatars'

    id = Column(Integer, primary_key=True)
    file_name = Column(String)

    def __init__(self, file_name):
	    self.file_name = file_name

    def get_all_avatars():
        try:
            return session.query(Avatar)
        except:
            session.rollback()
            return None       

#Class for the "badge_icons" table
class Icon(Base):
    __tablename__ = 'badge_icons'

    id = Column(Integer, primary_key=True)
    file_name = Column(String)

    def __init__(self, file_name):
	    self.file_name = file_name

    def get_all_icons():
        try:
            return session.query(Icon)
        except:
            session.rollback()
            return None                  

class Reset_Date(Base):
    __tablename__ = 'reset_date'
    
    reset_date = Column(Date, primary_key=True)
    
    def get_reset_date():
        try:
            return session.query(Reset_Date).first()
        except:
            session.rollback()
            return None
    
    def change_date(new_date):
        try:
            date = session.query(Reset_Date).first()
            date.reset_date = new_date
            session.commit()
            return True
        except:
            session.rollback()
            return False
            
