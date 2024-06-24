#importing different libraries
from flask import Flask,redirect,render_template,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine,text
from flask_login import UserMixin
from flask_login import login_required,logout_user,login_user,login_manager,LoginManager,current_user
from flask.globals import request,session
from werkzeug.security import generate_password_hash,check_password_hash
from flask.helpers import url_for
import json 
import os 
import logging
from flask_mail import Mail
from functools import wraps


engine=create_engine('mysql://root:@127.0.0.1/covid')
connection=engine.connect()

# mydatabase connection
local_server=True
app=Flask(__name__)
app.secret_key="gayathri"

# this is for getting the unique user access
login_manager=LoginManager(app)
login_manager.init_app(app)
login_manager.login_view='userlogin'


# app.config['SQLALCHEMY_DATABASE_URI']='mysql://username:password@loacalhost/databasename'
app.config['SQLALCHEMY_DATABASE_URI']='mysql://root:@127.0.0.1/covid'
db=SQLAlchemy(app)

#get the directory of the current file(main.py)
current_dir=os.path.dirname(__file__)

#construct the full path to config.json file
config_path=os.path.join(current_dir,'config.json')

with open(config_path,'r') as c:
    params=json.load(c)["params"]
    admin_user=params['user']
    admin_password=params['password']

#config particular mail app
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail=Mail(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    
               #<--------------start of database models------------------->

#model for checking data base model
class Test(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(50))

#model for usertable
class User(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    srfid=db.Column(db.String(20),unique=True)
    email=db.Column(db.String(100))
    dob=db.Column(db.String(1000))

#model for hospitaluser table
class Hospitaluser(UserMixin,db.Model):
    hid=db.Column(db.Integer,primary_key=True)
    hcode=db.Column(db.String(20))
    email=db.Column(db.String(100))
    password=db.Column(db.String(1000))

              #<---------------------end of database models--------------------->

              #<---------------------different routes--------------------------->

#route for home page
@app.route("/")
def home():
    return  render_template("index.html")

# @app.route("/usersignup")
# def usersignup():
#     return render_template("usersignup.html")

# @app.route("/userlogin")
# def userlogin():
#     return render_template("userlogin.html")

#route for usersignup page
@app.route("/usersignup",methods=['POST','GET'])
def usersignup():
    if request.method=='POST':
        srfid=request.form.get('srf')
        email=request.form.get('email')
        dob=request.form.get('dob')
        encpassword=generate_password_hash(dob)
        user=User.query.filter_by(srfid=srfid).first()
        emailUser=User.query.filter_by(email=email).first()
        if user or emailUser:
            flash("Email or srfid is already taken","warning")
            return render_template("usersignup.html")
        new_user = User(srfid=srfid, email=email, dob=encpassword)
        db.session.add(new_user)
        db.session.commit()
        
        flash("Signup Success Please Login","success")
        return render_template("userlogin.html")
        
    return render_template("usersignup.html")

#route for userlogin page
@app.route("/userlogin",methods=['POST','GET'])
def userlogin():
    if request.method=='POST':
        srfid=request.form.get('srf')
        dob=request.form.get('dob')
        user=User.query.filter_by(srfid=srfid).first()
        if user and check_password_hash(user.dob,dob):
            login_user(user)
            flash("Login Success","success")
            return render_template("index.html")
        else:
            flash("Login Failed","danger")
            return render_template("userlogin.html")
        
    return render_template("userlogin.html")

#route for admin page
@app.route("/admin",methods=['POST','GET'])
def admin():
    if request.method=='POST':
        username=request.form.get('username')
        password=request.form.get('password')
        if(username==params['user'] and password==params['password']):
            session['user']=username
            flash("login success","info")
            return render_template("addHosUser.html")
        else:
            flash("Invalid Credential","dander")

    return render_template("admin.html")

#route for adding hospital details
@app.route("/addHospitalUser",methods=['POST','GET'])
def hospitalUser():
    if('user' in session and session['user']==params['user']):       
        if request.method=='POST':
            hcode=request.form.get('hcode')
            email=request.form.get('email')
            password=request.form.get('password')
            encpassword=generate_password_hash(password)
            hcode=hcode.upper()
            emailUser=Hospitaluser.query.filter_by(email=email).first()
            if emailUser:
                flash("Email is already taken","warning")
                return render_template("addHosUser.html")
            else:
                new_user =Hospitaluser(hcode=hcode, email=email, password=encpassword)
                db.session.add(new_user)
                db.session.commit()
                mail.send_message('COVID CARE CENTRE',sender=params['gmail-user'],recipients=[email],body=f"Welcome to Bed Safe thanks for choosing us.Your Hospital Details are updated.\nYour Login Credentials are:\nEmail Address: {email}\nPassword: {password}\n\n\n Do not share your password\n\n\nThank You....")
                flash("Data is successfully added","info")
                return render_template("addHosUser.html")
    else:
        flash("Login and try again","warning")
        return render_template("admin.html")
    return render_template("addHosUser.html")

#route for hospitallogin page
@app.route("/hospitallogin",methods=['POST','GET'])
def hospitallogin():
    if request.method=='POST':
        email=request.form.get('email')
        password=request.form.get('password')
        user=Hospitaluser.query.filter_by(email=email).first()
        if user and check_password_hash(user.password,password):
            login_user(user)
            session['user-id']=user.id
            session['is_hospital']=True
            flash("Login Success","success")
            return render_template("index.html")
        else:
            flash("Invalid Credentials","danger")
            return render_template("hospitallogin.html")       
    return render_template("hospitallogin.html")


#logout method
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout Successful","warning")
    return redirect(url_for('userlogin'))

#logout method for admin
@app.route('/logoutadmin')
# @login_required
def logoutadmin():
    session.pop('user')
    flash("Logout Successful","primary")
    return render_template("admin.html")


# testing whether db is connected or not
@app.route("/test")
def test():
    try:
        a=Test.query.all()
        print(a)
        return f'MY DATABASE IS CONNECTED'
    except Exception as e:
        print(e)
        return f'MY DATABASE IS NOT CONNECTED{e}'

app.run(debug=True)