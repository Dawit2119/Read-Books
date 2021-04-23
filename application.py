import os,secrets,requests,datetime,pytz,json
from math import *
from flask import Flask, session,render_template,url_for,redirect,flash,abort,request,jsonify
from PIL import Image
from flask_login import login_user,current_user,logout_user,login_required,LoginManager
from forms import RegistrationForm,LoginForm,AccountUpdateForm
from flask_bcrypt import Bcrypt
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from functools import wraps


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
        return redirect(url_for('index'))
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
        if user and bcrypt.check_password_hash(user[4],form.password.data):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['email']= user[2]
            session['image_file'] = user[3]
            print(user)
            flash("You have been logged in!", 'success')
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
    
    

def login_required(f):  
    #Check Logged in by using session
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            flash("Please login to access this page!","info")
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/account", methods=['GET', 'POST'])
@login_required
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
                            image_file=image_file,form=form,username=user[1],email=user[2])  

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html',error=error),404
@app.route("/search")
def search_book():
    return render_template('search.html')

@app.route("/book", methods=["GET", "POST"])
@login_required
def book():
    if request.method == "POST":
        """ Get books results """

    if not request.form.get("book"):
        flash("please enter book information!",'danger')
        return redirect(url_for('search_book'))

    query = "%" + request.form.get("book") + "%"

    query = query.title()
    
    rows = db.execute("SELECT id,isbn, title, author, year FROM books WHERE \
                        isbn LIKE :query OR \
                        title LIKE :query OR \
                        author LIKE :query ORDER BY id DESC",
                        {"query": query})
    # Books not founded
    count = rows.rowcount
    if count == 0:
        flash("Sorry! No Result found!!",'danger')
        return redirect(url_for('search_book'))
    
    books = rows.fetchall()
    rates = []    
    
    # google books api
    for book in books:
            results = requests.get(f"https://www.googleapis.com/books/v1/volumes?q={book['isbn']}")
            book_info=json.loads(results.content)
            if book_info['totalItems'] != 0:
                for i in range(book_info['totalItems']):
                    if book_info['items'][i]['volumeInfo'].get('averageRating'):
                        rates.append(book_info['items'][i]['volumeInfo']['averageRating'])
                        break
            else:
                rates.append(1)
    for i in range(len(books)-len(rates)):
        rates.append(2)
    for i in range(len(rates)):
        rates[i] = int(round(rates[i],0))
        
    # print("Average Rating" ,book_info['items'][0]['volumeInfo']['averageRating'])
    # print("Image file" ,book_info['items'][0]['volumeInfo']['imageLinks']['smallThumbnail'])
        

    return render_template("book.html", books=books, count =count,rating=rates)


@app.route('/api/<isbn>')
@login_required
def api(isbn):
    book = db.execute(f"SELECT * from books WHERE isbn = '{isbn}'")
    if book.rowcount == 0:
        return render_template('page_not_found.html')
    book_info = book.fetchone()
    request = requests.get(f"https://www.googleapis.com/books/v1/volumes?q={isbn}")
    result = json.loads(request.content)
    average_rating = 0
    rating_count = 0
    if result['totalItems'] != 0:
        for i in range(len(result['items'])):
            if result['items'][i]['volumeInfo'].get('averageRating'):
                average_rating = result['items'][i]['volumeInfo'].get('averageRating')
            if result['items'][i]['volumeInfo'].get('ratingsCount'):
                rating_count = result['items'][i]['volumeInfo'].get('ratingsCount')
    
    book_information= {
        "title": book_info.title,
        "author":book_info.author,
        "year":book_info.year,
        "isbn":book_info.isbn,
        "averageRating":average_rating,
        "ratingCount":rating_count
    
        
    }
    return jsonify(book_information)
    

@app.route("/book/<isbn>", methods=['GET','POST'])
@login_required
def detail(isbn):

    if request.method == "POST":

        currentUser = session["username"]

        rating = int(request.form["rating"])
        comment = request.form.get("comment")


        if not request.form.get("comment"):
            flash('Please Leave Us a review!', 'danger')
            return redirect("/book/" + isbn)

        row = db.execute("SELECT id FROM books WHERE isbn = :isbn",
                        {"isbn": isbn})

        bookId = row.fetchone() 
        bookId = bookId[0]

        row2 = db.execute("SELECT * FROM reviews WHERE user_name = :user_name AND book_id = :book_id",
                    {"user_name": currentUser,
                     "book_id": bookId})

        # A review already exists
        if row2.rowcount == 1:
            flash(u'Sorry! You already submitted a review for this book!', 'danger');
            return redirect("/book/" + isbn)

        dt_utc = datetime.datetime.now(tz=pytz.UTC)


        db.execute("INSERT INTO reviews (user_name, book_id, comment, rating ,timezone) VALUES \
                    (:user_name, :book_id, :comment, :rating ,:timezone)",
                    {"user_name": currentUser, 
                    "book_id": bookId, 
                    "comment": comment, 
                    "rating": rating,
                    "timezone":dt_utc})

        db.commit()

        flash('Successfully reviewd!', 'success');
        return redirect("/book/" + isbn)
    else:

        row = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                        isbn = :isbn",
                        {"isbn": isbn})

        bookInfo = row.fetchall()

      
        
        """ Users reviews """
        row = db.execute("SELECT id FROM books WHERE isbn = :isbn",
                        {"isbn": isbn})
        book = row.fetchone() # (id,)
        book = book[0]
        request_api = json.loads(requests.get(f"https://www.googleapis.com/books/v1/volumes?q={isbn}").content)
        rating_api = 1
        if request_api['totalItems'] != 0:          
            for i in range(request_api['totalItems']):                
                if request_api['items'][i]['volumeInfo'].get('averageRating'):
                    rating_api = request_api['items'][i]['volumeInfo'].get('averageRating')

        results = db.execute("SELECT user_name, comment, rating, to_char(timezone, 'Mon DD, YYYY') as times\
                                FROM reviews WHERE book_id = :book ORDER BY id DESC",
                                {"book": book})

        reviews = results.fetchall()

        return render_template("review.html", bookInfo=bookInfo, reviews=reviews,rating_api=int(round(rating_api,0)))

if __name__ =='__main__':
    app.run(debug=True)