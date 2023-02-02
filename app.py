import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from helpers import login_required, pln, isPasswordStrong
from werkzeug.security import check_password_hash, generate_password_hash

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route('/')
@login_required
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()
    error = {}

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            error["username"] = True
            return render_template("login.html", error=error)

        # Ensure username was submitted
        if not request.form.get("password"):
            error["password"] = True
            return render_template("login.html", error=error)

        # Query database for username
        with sqlite3.connect("pieczarki.db") as con:
            cur = con.cursor()
            res = cur.execute("SELECT hash FROM users WHERE username = ?", [request.form.get("username")])
            hash = res.fetchone()
        # Ensure username exists and password is correct
        if hash is None or not check_password_hash(hash[0], request.form.get("password")):
            error["invalid"] = True
            return render_template("login.html", error=error)
        # Remember which user has logged in
        with sqlite3.connect("pieczarki.db") as con:
            cur = con.cursor()
            res = cur.execute("SELECT id FROM users WHERE username = ?", [request.form.get("username")])
            id = res.fetchone()
        session["user_id"] = id[0]

        # Redirect user to home page
        flash("Zostałeś zalogowany")
        return redirect("/")

    else:
        return render_template("login.html", error=error)

@app.route("/register", methods=["GET", "POST"])
def register():
        
    error = {}

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            error["username"] = True
            return render_template("register.html", error=error)

        # Ensure username isn't already used
        with sqlite3.connect("pieczarki.db") as con:
            cur = con.cursor()
            res = cur.execute("SELECT username FROM users")
            users = res.fetchall()

        for user in users:
            if user[0] == request.form.get("username"):
                error["taken"] = True
                return render_template("register.html", error=error)
        
        # Ensure username was submitted
        if not request.form.get("password"):
            error["password"] = True
            return render_template("register.html", error=error)

        # Ensure username was submitted
        if not request.form.get("confirmation"):
            error["confirmation"] = True
            return render_template("register.html", error=error)

        # Ensure confirmation and password are the same
        if not (request.form.get("confirmation") == request.form.get("password")):
            error["not equal"] = True
            return render_template("register.html", error=error)

        # Ensure password is strong enought
        if not isPasswordStrong(request.form.get("password")):
            return redirect("/register")
        
        with sqlite3.connect("pieczarki.db") as con:
            cur = con.cursor()
            cur.execute("INSERT INTO users (username, hash) VALUES(?, ?)",
                        (request.form.get("username"), generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)))
            con.commit()
            res = cur.execute("SELECT id FROM users WHERE username = ?", [request.form.get("username")])
            id = res.fetchone()
        
        session["user_id"] = id[0]
        # Redirect user to home page
        flash("Zostałeś zarejestrowany!")
        return redirect("/")


    else:
        return render_template("register.html", error=error)

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    flash("Wylogowałeś się")
    return redirect("/login")