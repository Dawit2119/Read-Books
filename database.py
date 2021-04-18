import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
# database uri
""""
export DATABASE_URL=postgresql://xiyqayicucdjoo:0eccd743ed6c5e9a80251399d15c8ccc427d97dea0b6dde205880aa00eb6a58f@ec2-35-174-35-242.compute-1.amazonaws.com:5432/detas6rlmlsbrl
"""
def main():
	#create table users
	db.execute("""CREATE TABLE IF NOT EXISTS users(
    				id serial primary key,
    				username text unique NOT NULL,
					email text unique NOT NULL,
					image_file text Default 'default.png',
					password text NOT NULL
    				)""")

	print("table users created\n")

	#create table books
	db.execute("""CREATE TABLE IF NOT EXISTS books(
				    id serial primary key,
				    isbn char(10) unique NOT NULL,
				    title text NOT NULL,
				    author text NOT NULL,
				    year char(4) NOT NULL)""")

	print("table books created\n")
	#create table reviews
	db.execute("""CREATE TABLE IF NOT EXISTS reviews(
				    id serial primary key,
				    user_name text references users(username),
				    book_id integer references books(id),
				    rating integer NOT NULL ,
				    comment varchar(1500) NOT NULL,
				    timezone timestamptz)""")

	print("table reviews created\n")
	db.commit()
# my_file = open("books.csv")
# books = csv.reader(my_file)
# for isbn,title,author,year in books:
#     db.execute("insert into books(isbn,title,author,year) values(:isbn,:title,:author,:year)",
#     {"isbn": isbn, "title": title,"year": year,"author": author})
#     print(f"Added book {title} by {author} in {year}: isbn: {isbn}")
# print("Books entered successfully")
# db.commit()
    	 		 
if __name__ == "__main__":
    main()
