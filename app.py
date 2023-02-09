from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from helpers import login_required, pln, isPasswordStrong
from werkzeug.security import check_password_hash, generate_password_hash

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pieczarki.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 

Session(app)
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    hash = db.Column(db.String(100), nullable=False)
    cultivations = db.relationship('Cultivation', backref='user', lazy=True)
    halls = db.relationship('Hall', backref='user', lazy=True)

class Cultivation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hall_id = db.Column(db.Integer, db.ForeignKey('hall.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    manufacturer = db.Column(db.String(50), nullable=False)
    phase = db.Column(db.String(50), nullable=False)
    cubes_count = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(100))

class Hall(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    max_cubes = db.Column(db.Integer)
    area = db.Column(db.Float)
    #empty = db.Column(db.Boolean default=True)
    cultivations = db.relationship('Cultivation', backref='hall', lazy=True)


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
    cultivations = Cultivation.query.filter_by(user_id = session["user_id"]).all()
    return render_template("index.html", cultivations=cultivations)


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
        hash = db.session.query(User.hash).filter_by(username = request.form.get("username")).scalar()
        
        # Ensure username exists and password is correct
        if hash is None or not check_password_hash(hash, request.form.get("password")):
            error["invalid"] = True
            return render_template("login.html", error=error)
        
        # Remember which user has logged in
        session["user_id"] = db.session.query(User.id).filter_by(username = request.form.get("username")).scalar()
        
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
        users = User.query.all()

        for user in users:
            if user.username == request.form.get("username"):
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
        
        user = User(
            username = request.form.get("username"),
            hash = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
        )
        db.session.add(user)
        db.session.commit()
        session["user_id"] = db.session.query(User.id).filter_by(username = user.username).scalar()
        
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


@app.route("/newcultivation", methods=["GET", "POST"])
@login_required
def newcultivation():

    forms =["date", "hall_id", "manufacturer", "phase", "cubes_count", "price"]
    errors = []
    answ = {"user_id":session["user_id"]}
    if request.method == "POST": 
        for form in forms:
            if not request.form.get(form):
                errors.append(form)

        if errors:
            return render_template("newcultivation.html", errors=errors)

        for form in forms:
            answ[form] = request.form.get(form)

        cultivation = Cultivation(
            user_id = answ["user_id"],
            hall_id = answ["hall_id"],
            date = datetime.strptime(answ["date"], '%Y-%m-%d').date(),
            manufacturer = answ["manufacturer"],
            phase = answ["phase"],
            cubes_count = answ["cubes_count"],
            price = answ["price"]
        )
        db.session.add(cultivation)
        db.session.commit()

        flash("Uprawa została stworzona")
        return redirect("/")

    else:

        halls = Hall.query.filter_by(user_id = session["user_id"]).all()
        return render_template("newcultivation.html",errors=errors, halls=halls)

@app.route('/hall')
@login_required
def hall():

    halls = Hall.query.filter_by(user_id = session["user_id"]).all()
    return render_template("hall.html", halls=halls)


@app.route('/newhall', methods=["GET", "POST"])
@login_required
def newhall():

    error = {}

    if request.method == "POST":

        if not request.form.get("name"):
            error["name"] = True
            return render_template("newhall.html", error=error)

        if not request.form.get("max_cubes"):
            error["max_cubes"] = True
            return render_template("newhall.html", error=error)

        if not request.form.get("area"):
            error["area"] = True
            return render_template("newhall.html", error=error)

        hall = Hall(
            user_id = session["user_id"],
            name = request.form.get("name"),
            max_cubes = request.form.get("max_cubes"),
            area = request.form.get("area")
        )
        db.session.add(hall)
        db.session.commit()

        flash("Pieczarkarnia została dodana")
        return redirect("/hall")

    else:
        return render_template("newhall.html", error=error)


"""@app.route('/cultivation/<int:cultivation_id>')
def cultivation_detail(cultivation_id):
    cultivation = Cultivation.query.get(cultivation_id)
    return render_template('cultivation_detail.html', cultivation=cultivation)"""

