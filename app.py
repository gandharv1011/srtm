from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ---------------------
# POSTGRESQL DATABASE CONFIG (Render)
# ---------------------

database_url = os.environ.get("DATABASE_URL")

# Fix for Render old postgres:// format
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------------
# DATABASE TABLES
# ---------------------

class Collection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    amount = db.Column(db.Float)
    mode = db.Column(db.String(20))
    date = db.Column(db.DateTime, default=datetime.now)


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    amount = db.Column(db.Float)
    mode = db.Column(db.String(20))
    date = db.Column(db.DateTime, default=datetime.now)


# Create tables automatically
with app.app_context():
    db.create_all()

# ---------------------
# ADMIN LOGIN
# ---------------------

ADMIN_ID = "srtm"
ADMIN_PASSWORD = "srtm1234"

# ---------------------
# DASHBOARD
# ---------------------

@app.route("/")
def dashboard():
    collections = Collection.query.all()
    expenses = Expense.query.all()

    total_cash = 0
    total_online = 0

    today_cash = 0
    today_online = 0

    today_date = datetime.now().date()

    for c in collections:
        mode = c.mode.strip().lower()

        # Total calculation
        if mode == "cash":
            total_cash += c.amount
        elif mode == "online":
            total_online += c.amount

        # Today's collection calculation
        if c.date.date() == today_date:
            if mode == "cash":
                today_cash += c.amount
            elif mode == "online":
                today_online += c.amount

    total_expense = sum(e.amount for e in expenses)
    net = total_cash + total_online - total_expense

    today_total = today_cash + today_online

    return render_template(
        "dashboard.html",
        collections=collections,
        expenses=expenses,
        total_cash=total_cash,
        total_online=total_online,
        total_expense=total_expense,
        net=net,
        today_cash=today_cash,
        today_online=today_online,
        today_total=today_total
    )

# ---------------------
# LOGIN
# ---------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["userid"] == ADMIN_ID and request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")

# ---------------------
# ADD COLLECTION
# ---------------------

@app.route("/add_collection", methods=["POST"])
def add_collection():
    if "admin" in session:
        new = Collection(
            name=request.form["name"],
            amount=float(request.form.get("amount", 0)),
            mode=request.form["mode"],
            date=datetime.now()
        )
        db.session.add(new)
        db.session.commit()
    return redirect("/")

# ---------------------
# ADD EXPENSE
# ---------------------

@app.route("/add_expense", methods=["POST"])
def add_expense():
    if "admin" in session:
        new = Expense(
            name=request.form["name"],
            amount=float(request.form.get("amount", 0)),
            mode=request.form["mode"],
            date=datetime.now()
        )
        db.session.add(new)
        db.session.commit()
    return redirect("/")

# ---------------------
# DELETE
# ---------------------

@app.route("/delete/<type>/<int:id>")
def delete(type, id):
    if "admin" in session:
        if type == "collection":
            item = Collection.query.get(id)
        else:
            item = Expense.query.get(id)

        db.session.delete(item)
        db.session.commit()

    return redirect("/")

# ---------------------
# EDIT
# ---------------------

@app.route("/edit/<type>/<int:id>", methods=["GET", "POST"])
def edit(type, id):
    if "admin" not in session:
        return redirect("/")

    if type == "collection":
        item = Collection.query.get(id)
    else:
        item = Expense.query.get(id)

    if request.method == "POST":
        item.name = request.form["name"]
        item.amount = float(request.form.get("amount", 0))
        item.mode = request.form["mode"]
        item.date = datetime.strptime(request.form["date"], "%Y-%m-%d")
        db.session.commit()
        return redirect("/")

    return render_template("edit.html", item=item, type=type)

# ---------------------
# RUN
# ---------------------

if __name__ == "__main__":
    app.run()

