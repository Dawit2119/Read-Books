from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
class User(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(200), nullable=False, default='default.png')
    password = db.Column(db.String(200), nullable=False)

    def __init__(self,username,email,password):
        self.username = username
        self.email = email
        self.password = password
        
    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"
