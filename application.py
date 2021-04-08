import os,secrets
from flask import Flask, session,render_template,url_for,redirect,flash,abort,request
from flask_session import Session
from PIL import Image
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user,current_user,logout_user,login_required,LoginManager
from forms import RegistrationForm,LoginForm,AccountUpdateForm
from flask_bcrypt import Bcrypt
from models import User

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password29@localhost/newdatabase'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/")
def index():
    return render_template("layout.html",title="home")

@app.route("/about")
def about():
    return render_template("about.html",title="about")

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data,email=form.email.data,password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash("Your account is created successfully! you are now able to login", "success")
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and bcrypt.check_password_hash(user.password,form.password.data):
                login_user(user,remember=form.remember.data)
                flash('You have been logged in!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _,fileext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + fileext
    picture_path = os.path.join(app.root_path,'static/profilePics/',picture_fn)
    output_size = (125,125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn
    
    
    

@app.route("/logout")
def logout():
     logout_user()
     return redirect(url_for('index'))

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
     form = AccountUpdateForm()
     if form.validate_on_submit():
         if form.profile_picture.data:
             profile_picture = save_picture(form.profile_picture.data)
             current_user.image_file = profile_picture
         current_user.username = form.username.data + " hello"
         current_user.email = form.email.data
         db.session.commit()
         flash("Your Account is successfully updated!","success")
         return redirect(url_for('account'))
     else:
         request.methods = 'GET'
         form.username.data = current_user.username
         form.email.data = current_user.email 
     image_file = url_for('static',filename= 'profilePics/' + current_user.image_file)
     return render_template('account.html',
                            image_file=image_file,form=form,title='account page')  
