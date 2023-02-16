from flask import Flask, render_template, session
from flask_session import Session
import re
from flask import Flask, render_template, session, request, redirect
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL



app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = 'super secret key'

db = SQL("sqlite:///final-project.db")


Session(app)

@app.route("/")
def index():
    session.clear()
    session["Admin"] = 1
    session["user_id"] = 1
    return render_template("index.html")

@app.route("/billGen")
def billGen():
    people = db.execute("SELECT * FROM person WHERE person_id = ?", "2")
    return render_template("billGen.html", people = people)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("error.html" , errormsg = "must provide username ", code = 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("error.html" , errormsg = "must provide password ", code = 403)

        # Query database for username
        rows = db.execute("SELECT * FROM Credentials WHERE username = ?" ,request.form.get("username"))
        # Ensure username exists and password is correct
        if len(rows) != 1 or not  (rows[0]["password"]==  request.form.get("password")):
            return render_template( "error.html" , errormsg = "invalid username and/or password", code = 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["person_id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    
    if request.method =="POST":
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        email = request.form.get("email")
        phone = request.form.get("phone")
        isadmin = request.form.get("isadmin")
        person = (firstname,lastname,email,phone,isadmin)
        print(person)
        if isadmin == '1':
            db.execute("INSERT INTO Person (firstname ,lastname,email_id,phone_number,isAdmin) VALUES (?,?,?,?,?)" , firstname,lastname,email,phone,isadmin)
        else:
            db.execute("INSERT INTO Person (firstname ,lastname,email_id,phone_number) VALUES (? ,?,?,?)" , firstname,lastname,email,phone)
        
        person_id = db.execute("Select person_id from Person where phone_number = ?" , phone)
        person_id = person_id[0]
        person_id = person_id["person_id"]
        
        return render_template("Credentials.html",person_id = person_id)

    else:
        return render_template("register.html")
    
@app.route("/credentials", methods=["GET", "POST"])
def credentials():
    if request.method == "POST":
        person_id = request.form.get("person_id")
        username = request.form.get("username")
        password = request.form.get("password")
        db.execute("INSERT INTO Credentials(person_id,username,password) VALUES(?,?,?)" , person_id , username , password)
        return render_template("login.html")
    

@app.route("/additem" , methods=["GET", "POST"])
def additem():
    if request.method == "POST":
        itemname = request.form.get("itemname")
        price = request.form.get("price")
        quantity = request.form.get("quantity")
        category_id = request.form.get("category_id")
        if category_id == "0":
            new_category = request.form.get("newcategory")
            print(new_category)
            db.execute("INSERT INTO Category(category_name) VALUES(?)" , new_category)
            category_id = db.execute("SELECT category_id from Category where category_name = ?" , new_category)
            category_id = category_id[0]
            category_id = category_id["category_id"]

        db.execute("INSERT INTO Item(itemname,price,quantity,category_id) VALUES(?,?,?,?)" , itemname , price ,quantity, category_id)
        return redirect("/")
    else:
        category = db.execute("SELECT * from Category")
        print(category)
        return render_template("additem.html" , category = category)

