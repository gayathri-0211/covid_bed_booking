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

# mydatabase connection
local_server=True
app=Flask(__name__)
app.secret_key="gayathri"

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
    if session.get("is_hospital"):
        return Hospitaluser.query.get(int(user_id))
    else:
        return User.query.get(int(user_id))
    
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

engine=create_engine('mysql://root:@127.0.0.1/covid')
connection=engine.connect()

def hospitallogin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_hospital', False):
            flash("You need to be logged in to access this page.", "danger")
            return redirect(url_for('hospitallogin'))
        return f(*args, **kwargs)
    return decorated_function
    
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
    id=db.Column(db.Integer,primary_key=True)
    hcode=db.Column(db.String(20))
    email=db.Column(db.String(100))
    password=db.Column(db.String(1000))

#model for hospitaldata table
class Hospitaldata(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    hcode=db.Column(db.String(200),unique=True)
    hname=db.Column(db.String(200))
    normalbeds=db.Column(db.Integer)
    hicubeds=db.Column(db.Integer)
    icubeds=db.Column(db.Integer)
    ventbeds=db.Column(db.Integer)

#model for bookingpatient table
class Bookingpatient(db.Model,UserMixin):
    id=db.Column(db.Integer,primary_key=True)
    srfid=db.Column(db.String(50),unique=True)
    bedtype=db.Column(db.String(50))
    hcode=db.Column(db.String(50))
    spo2=db.Column(db.Integer)
    pname=db.Column(db.String(50))
    pphone=db.Column(db.String(12))
    paddress=db.Column(db.String(100))

class Trig(db.Model,UserMixin):
    id=db.Column(db.Integer,primary_key=True)
    hcode=db.Column(db.String(200))
    normalbeds=db.Column(db.Integer)
    hicubeds=db.Column(db.Integer)
    icubeds=db.Column(db.Integer)
    vbeds=db.Column(db.Integer)
    querys=db.Column(db.String(50))
    date=db.Column(db.String(50))

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
                mail.send_message('COVID CARE CENTRE',sender=params['gmail-user'],recipients=[email],body=f"Welcome to Bed Safe thanks for choosing us.Your Hospital Details are updated.\nYour Login Credentials are:\nEmail Address: {email}\nPassword: {password}\nHospital Code: {hcode}\n\n\n Do not share your password\n\n\nThank You....")
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
            session['user_id']=user.id
            session['is_hospital']=True
            flash("Login Success","success")
            return render_template("index.html")
        else:
            flash("Invalid Credentials","danger")
            return render_template("hospitallogin.html")       
    return render_template("hospitallogin.html")

#route for adding data of hospital
@app.route("/addhospitalinfo",methods=['POST','GET'])
def addhospitalinfo():
    email=current_user.email
    posts=Hospitaluser.query.filter_by(email=email).first()
    code=posts.hcode
    postsdata=Hospitaldata.query.filter_by(hcode=code).first()
    if request.method=='POST':
        hcode=request.form.get('hcode')
        hname=request.form.get('hname')
        normalbeds=request.form.get('normalbeds')
        hicubeds=request.form.get('hicubeds')
        icubeds=request.form.get('icubeds')
        ventbeds=request.form.get('ventbeds')
        hcode=hcode.upper()
        huser=Hospitaluser.query.filter_by(hcode=hcode).first()
        hduser=Hospitaldata.query.filter_by(hcode=hcode).first()
        if hduser:
            flash("Data is already present you can update it","primary")
            return render_template("hospitaldata.html",postsdata=postsdata)
        if huser:
            new_user=Hospitaldata(hcode=hcode,hname=hname,normalbeds=normalbeds,hicubeds=hicubeds,icubeds=icubeds,ventbeds=ventbeds)
            db.session.add(new_user)
            db.session.commit()
            flash("Data is added","success")
        else:
            flash("Hospital code doesn't exist","warning")
    return render_template("hospitaldata.html",postsdata=postsdata)
        
            
#route for editing hospital data
@app.route("/hedit/<string:id>",methods=['POST','GET'])
@login_required
def hedit(id):
    posts=Hospitaldata.query.filter_by(id=id).first()
    if request.method=='POST':
        hcode=request.form.get('hcode')
        hname=request.form.get('hname')
        normalbeds=request.form.get('normalbeds')
        hicubeds=request.form.get('hicubeds')
        icubeds=request.form.get('icubeds')
        ventbeds=request.form.get('ventbeds')
        hcode=hcode.upper()
        sql = text(f"UPDATE hospitaldata SET hcode=:hcode, hname=:hname, normalbeds=:normalbeds, hicubeds=:hicubeds, icubeds=:icubeds, ventbeds=:ventbeds WHERE id=:id")
        db.session.execute(sql, {"hcode": hcode, "hname": hname, "normalbeds": normalbeds, "hicubeds": hicubeds, "icubeds": icubeds, "ventbeds": ventbeds, "id": id})
        db.session.commit()
        flash("Data is updated","success")
        return redirect("/addhospitalinfo")
    return render_template("hedit.html",posts=posts)

#route for deleting hospital data
@app.route("/hdelete/<string:id>",methods=['POST','GET'])
@login_required
def hdelete(id):
    # Query the record by ID
    record_to_delete = Hospitaldata.query.get_or_404(id)
    try:
        # Delete the record
        db.session.delete(record_to_delete)
        db.session.commit()
        flash("Data deleted successfully", "success")
    except Exception as e:
        db.session.rollback()  # Roll back the changes on error
        flash(f"Failed to delete data: {e}", "danger")
    return redirect(url_for('addhospitalinfo'))

#route for slotbooking page
@app.route("/slotbooking",methods=['POST','GET'])
@login_required
def slotbooking():
    query = Hospitaldata.query.all()
    if request.method=="POST":
        srfid = request.form.get('srfid')
        bedtype = request.form.get('bedtype')
        hcode = request.form.get('hcode')
        spo2 = request.form.get('spo2')
        pname = request.form.get('pname')
        pphone = request.form.get('pphone')
        paddress = request.form.get('paddress')
        code = hcode
        try:
            # Query the record by hcode
            hospital_record = Hospitaldata.query.filter_by(hcode=code).first()
            if not hospital_record:
                flash("Hospital record not found", "danger")
                return redirect(url_for('some_view'))  # Replace 'some_view' with the appropriate view name
            # Update the appropriate bed type
            if bedtype == "Normalbeds":
                if hospital_record.normalbeds > 0:
                    hospital_record.normalbeds -= 1
                    booking_successful = True
                else:
                    booking_successful = False
                    flash("No normal beds available in this hospital", "warning")
            elif bedtype == "HICUbed":
                if hospital_record.hicubeds > 0:
                    hospital_record.hicubeds -= 1
                    booking_successful = True
                else:
                    booking_successful = False
                    flash("No HICU beds available in this hospital", "warning")
            elif bedtype == "ICUbed":
                if hospital_record.icubeds > 0:
                    hospital_record.icubeds -= 1
                    booking_successful = True
                else:
                    booking_successful = False
                    flash("No ICU beds available in this hospital", "warning")
            elif bedtype == "Ventilatorbed":
                if hospital_record.ventbeds > 0:
                    hospital_record.ventbeds -= 1
                    booking_successful = True
                else:
                    booking_successful = False
                    flash("No ventilator beds available in this hospital", "warning")
            else:
                booking_successful = False
                flash("Invalid bed type", "danger")
            if booking_successful:
                db.session.commit()
                # Insert patient data into Bookingpatient table
                new_patient = Bookingpatient(
                    srfid=srfid,
                    bedtype=bedtype,
                    hcode=hcode,
                    spo2=spo2,
                    pname=pname,
                    pphone=pphone,
                    paddress=paddress
                )
                db.session.add(new_patient)
                db.session.commit()
                flash("Your bed slot is booked successfully", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", "danger")
    return render_template("booking.html", query = query)

# patient details page routing
@app.route("/pdetails", methods=['GET'])
def pdetails():
    code=current_user.srfid
    data=Bookingpatient.query.filter_by(srfid=code).first()
    return render_template("details.html",data=data)
  
@app.route("/triggers")
def triggers():
    query=Trig.query.all()
    return render_template("triggers.html",query=query)

            # <------------routing end------>
    
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

# Hospital User logout page routing
@app.route("/logouthospitaluser")
def logouthospitaluser():
    session.clear()
    # session.pop('user_id', None)  # Clear user ID from session
    flash("You have been logged out", "info")
    return redirect(url_for('hospitallogin'))  # Redirect to login page after logout

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