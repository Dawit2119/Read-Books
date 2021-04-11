import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
	#create table users
	db.execute("""CREATE TABLE users(
    				id serial primary key,
    				username text unique NOT NULL,
					email text unique NOT NULL,
					image_file text Default 'default.png',
					password text NOT NULL
    				)""")

	print("table users created\n")

	#create table books
	db.execute("""CREATE TABLE books(
				    id serial primary key,
				    isbn char(10) unique NOT NULL,
				    title text NOT NULL,
				    author text NOT NULL,
				    year char(4) NOT NULL)""")

	print("table books created\n")
	#create table reviews
	db.execute("""CREATE TABLE reviews(
				    id serial primary key,
				    user_name text references users(username),
				    book_id integer references books(id),
				    rating integer NOT NULL ,
				    comment varchar(1500) NOT NULL,
				    timezone timestamptz)""")

	print("table reviews created\n")
	db.commit()
    	 		 
if __name__ == "__main__":
    main()
