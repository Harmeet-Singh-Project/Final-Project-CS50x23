from flask import Flask, render_template, session
from flask_session import Session
import re
from flask import Flask, render_template, session, request, redirect, make_response
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date
from cs50 import SQL
import json
import math


app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = 'super secret key'

db = SQL("sqlite:///final-project.db")


Session(app)

@app.route("/")
def index():
    
    session["Admin"] = 1
    session["cart"] = {
        "customer_name" : "",
        "phone_number" : "",
        "cart_item" : [], 
        "totalAmount" : 0,
        "printed" : ""
    }
    
    return render_template("index.html")

@app.route("/billGen", methods=["GET", "POST"])
def billGen():
    if session["cart"]["printed"] == "printed":
        session["cart"] = {
            "customer_name" : "",
            "phone_number" : "",
            "cart_item" : [], 
            "totalAmount" : 0,
            "printed" : ""
        }
    if request.method == 'POST':
        if request.form["billGen-button"] == "Add Item":
            print("Add item")
            session["cart"]["customer_name"] = request.form.get("customer-name")
            session["cart"]["phone_number"] = request.form.get("customer-phoneNo")
            item_id = request.form.get("item")
            discount = request.form.get("discount")
            quantity = request.form.get("item-weight")
            item = db.execute("SELECT * FROM Item WHERE item_id = ?", item_id)
            item = item[0]

            totalPrice = request.form.get("total-price")
            total = float(session["cart"]["totalAmount"])
            total = total + float(totalPrice)
            
            cart_item = {
                "item_id" : item_id,
                "name" : item["itemname"],
                "pricePerKG" : item["price"],
                "quantity" : quantity,
                "discount" : discount,
                "totalPrice" : totalPrice
            }

            itemList = []
            itemList = list(session["cart"]["cart_item"])
            present = False
            for tempItem in itemList:
                if tempItem["item_id"] == item_id:
                    tempItem["quantity"] = int(tempItem["quantity"]) + int(quantity)
                    tempItem["totalPrice"] = float(tempItem["totalPrice"]) + float(totalPrice)
                    tempItem["discount"] = float((float(tempItem["discount"]) + float(discount)) / 2.0  )
                    present = True    
            
            if not present:
                itemList.append(cart_item)

            session["cart"]["cart_item"] = itemList
            session["cart"]["totalAmount"] = total

            items = db.execute("SELECT * FROM Item")
            return render_template("billGen.html", items = items)
        
    else:
        items = db.execute("SELECT * FROM Item")
        return render_template("billGen.html", items = items)

@app.route("/getItem")
def getItem():
    item_id = request.args.get("item")
    items = db.execute("SELECT * FROM Item WHERE item_id = ?", item_id)
    return json.dumps(items[0])

@app.route("/deleteItem")
def deleteItem():
    itemList = session["cart"]["cart_item"]
    item_id = request.args.get("item")
    tempitem = []
    total = 0
    for item in itemList:
        if item["item_id"] != item_id:
            tempitem.append(item)
            total = total + float(item["totalPrice"])
    
    session["cart"]["cart_item"] = tempitem
    session["cart"]["totalAmount"] = total

    return redirect("/billGen")

@app.route("/billLayout")
def billLayout():
    cart = session["cart"]["cart_item"]
    db.execute(
        "INSERT INTO transactions(user_id, transaction_towards, amount, reason, withdrawal_or_deposit) VALUES (?, ?, ?, ?, ?)",
            session["user_id"], session["cart"]["customer_name"], session["cart"]["totalAmount"], "Puchase", "deposit")

    for item in cart:
        db.execute("INSERT INTO TodaysSoldItem (itemName, quantity) VALUES(?, ?)", item["name"], item["quantity"])

    for item in session["cart"]["cart_item"]:
        db.execute("UPDATE Item SET quantity = quantity - ? WHERE item_id = ?", int(item["quantity"]), int(item["item_id"]))
    session["cart"] = {
        "customer_name" : "",
        "phone_number" : "",
        "cart_item" : [], 
        "totalAmount" : 0,
        "printed" : ""
    }
    return render_template("billLayout.html", cart = cart)

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
        if len(rows) != 1 or not  check_password_hash(rows[0]["password"], request.form.get("password")):
            return render_template( "error.html" , errormsg = "invalid username and/or password", code = 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["person_id"]
        session["user_name"] = request.form.get("username")
        session["today_date"] = date.today()

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
        db.execute("INSERT INTO Credentials(person_id,username,password) VALUES(?,?,?)" , person_id , username , generate_password_hash(password))
        return render_template("login.html")
    

@app.route("/additem" , methods=["GET", "POST"])
def additem():
    if request.method == "POST":
        itemname = request.form.get("itemname")
        price = request.form.get("price")
        quantity = request.form.get("quantity")
        category_id = request.form.get("category_id")
        retail_discount = request.form.get("retail_discount")
        wholesale_discount = request.form.get("wholesale_discount")
        item = db.execute("SELECT * from Item")
        for i in item:
            print(itemname.upper())
            print(str(i["itemname"]).upper())

            if (itemname.upper()) == str(i["itemname"]).upper():
                item_id = (i["item_id"])
                db.execute("UPDATE Item  SET price = ? , itemname = ? , quantity = ? , category_id = ? , retail_discount = ?,wholesale_discount = ?  where item_id = ? " , price , itemname,quantity,category_id,retail_discount,wholesale_discount, item_id)
                print(i["itemname"])
                return redirect("/")
                       
        

        if category_id == "0":
            new_category = request.form.get("newcategory")
            db.execute("INSERT INTO Category(category_name) VALUES(?)" , new_category)
            category_id = db.execute("SELECT category_id from Category where category_name = ?" , new_category)
            category_id = category_id[0]
            category_id = category_id["category_id"]

        db.execute("INSERT INTO Item(itemname,price,quantity,category_id,retail_discount,wholesale_discount) VALUES(?,?,?,?,?,?)" , itemname , price ,quantity, category_id,retail_discount,wholesale_discount)
        return redirect("/")
    else:
        category = db.execute("SELECT * from Category")
        return render_template("additem.html" , category = category)
    

@app.route("/addworker" , methods=["GET", "POST"])
def addworker():
    if request.method == "POST":
        fullname = request.form.get("fullname")
        phone = request.form.get("phone")
        address = request.form.get("address")
        salary = request.form.get("salary")
        workers = db.execute("SELECT * from Worker")
        db.execute("INSERT INTO Worker(fullname,phone,address,salary) VALUES(?,?,?,?)" , fullname , phone ,address, salary)
        return redirect("/")
        
    return render_template("workers.html")

@app.route("/moneywithdrawal" , methods=["GET", "POST"])
def withdrawmoney():
    if request.method == "POST":
        transaction_towards = request.form.get("towhom")
        amount = request.form.get("amount")
        reason = request.form.get("reason")
        transaction_towards = request.form.get("towhom")
        db.execute("INSERT INTO transactions(user_id,transaction_towards,amount,reason,withdrawal_or_deposit) VALUES(?,?,?,?,?)" , session["user_id"] ,transaction_towards, amount ,reason, "withdrawal")
        return redirect("/")
    else:
        return render_template("moneywithdrawal.html")


@app.route("/purchaseDesktop" , methods=["GET", "POST"])
def purchaseDesktop():
    items = db.execute("SELECT DISTINCT(itemname) as item_name, SUM(quantity) as total_quantity FROM TodaysSoldItem WHERE tran_date = CURRENT_DATE GROUP BY itemname")
    
    productWiseData = []
    productWiseDataLabels = []
    total = 0
    for item in items:
        total = total + int(item["total_quantity"])

    for item in items:
        productWiseDataLabels.append(item["item_name"])
        productWiseData.append(math.ceil( int((int(item["total_quantity"]) / total) * 100)))

    dates = db.execute("SELECT DISTINCT(tran_date) AS tran_date FROM TodaysSoldItem WHERE tran_date >= date('now', '-7 days')")
    top_items = db.execute("SELECT itemName, SUM(quantity) AS total_quantity FROM TodaysSoldItem GROUP BY itemName HAVING tran_date >= date('now', '-7 days') ORDER BY total_quantity LIMIT 5")

    list_dates = []

    for date in dates:
        list_dates.append(date["tran_date"])

    data = []

    for item in top_items:
        temp_Item = {
            "name" : "",
            "data" : []
        }
        data.append(temp_Item)

    count = 0
    print(top_items)
    for item in top_items:
        data[count]["name"] = item["itemName"]
        for date in dates:
            tempList = data[count]["data"]
            temp = db.execute("SELECT SUM(quantity) AS quantity FROM TodaysSoldItem WHERE itemName = ? and tran_date = ?", item["itemName"], date["tran_date"])
            if temp[0]["quantity"] is None or len(temp) == 0:
                tempList.append(0)
            else:
                tempList.append(int(temp[0]["quantity"]))
            data[count]["data"] = tempList
        count += 1

    query = str("SELECT p.firstname || ' ' || p.lastname as username, tran.transaction_towards, tran.amount, tran.transaction_time, tran.reason, tran.withdrawal_or_deposit FROM credentials c JOIN Person p JOIN transactions tran ON c.person_id = p.person_id AND tran.user_id = p.person_id WHERE tran.transaction_time >= CURRENT_DATE")
    transactions = db.execute(query)
    total = 0
    for transaction in transactions:
        total += int(transaction["amount"])

    return render_template("purchaseDesktop.html", productWiseData = json.dumps(productWiseData), productWiseDataLabels = json.dumps(productWiseDataLabels), pastSevenproductWiseData = json.dumps(data), dates = json.dumps(list_dates), transactions = transactions, total_amount = total)