import os,secrets
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, session,render_template,url_for,redirect,flash,abort,request
from PIL import Image
from flask_login import login_user,current_user,logout_user,login_required,LoginManager
from forms import RegistrationForm,LoginForm,AccountUpdateForm
from flask_bcrypt import Bcrypt
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = 'secret key'
# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.execute(f"SELECT * FROM user WHERE user_id = '{user_id}'")

@app.route("/")
def index():
    return render_template("layout.html",title="home")

@app.route("/about")
def about():
    return render_template("about.html",title="about")

@app.route("/register", methods=['GET', 'POST'])
def register():
    if session.get("user_id"):
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        db.execute(f"insert into users(username,email,password) values ('{form.username.data}','{form.email.data}','{hashed_password}')")
        db.commit()
        flash("Your account is created successfully! you are now able to login", "success")
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    logged = session.get("user_id")
    print(logged)
    if logged:
        return redirect(url_for('index'))
    # session.clear()
    form = LoginForm()
    if form.validate_on_submit():     
        user = db.execute(f"""SELECT * FROM users WHERE email ='{form.email.data}'""").fetchone()
        db.commit()
        if user and bcrypt.check_password_hash(user[4],form.password.data):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['email']= user[2]
            session['image_file'] = user[3]
            print(user)
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
     session.clear()
     return redirect(url_for('index'))

@app.route("/account", methods=['GET', 'POST'])
# @login_required
def account():
     form = AccountUpdateForm()
     session['username'] = form.username.data
     session['email'] = form.email.data
     if form.validate_on_submit():
         if form.profile_picture.data:
             profile_picture = save_picture(form.profile_picture.data)
             db.execute(f"UPDATE users SET image_file = '{profile_picture}' WHERE id = {int(session.get('user_id'))}")
         db.execute(f"UPDATE users SET username = '{form.username.data}' WHERE id = {int(session.get('user_id'))}")
         db.execute(f"UPDATE users SET email = '{form.email.data}' WHERE id = {int(session.get('user_id'))}")
         db.commit()
         flash("Your account is updated",'info')
         return redirect(url_for('account'))
     else:
         request.methods = 'GET'
         user = db.execute(f"SELECT * FROM users WHERE id = '{session.get('user_id')}'").fetchone()
         db.commit()
         form.username.data = user[1]
         form.email.data = user[2]
     image_file = url_for('static',filename= 'profilePics/' + user[3])
     return render_template('account.html',
                            image_file=image_file,form=form)  
 
if __name__ =='__main__':
    app.run(debug=True)