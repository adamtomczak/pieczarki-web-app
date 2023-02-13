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
    date = db.Column(db.Date, nullable=False, default=datetime.now)
    manufacturer = db.Column(db.String(50), nullable=False)
    phase = db.Column(db.String(50), nullable=False)
    cubes_count = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(100))
    peat_date = db.Column(db.Date)
    shock_date = db.Column(db.Date)
    harvests = db.relationship('Harvest', backref='cultivation', lazy=True)
    costs = db.relationship('Cost', backref='cultivation', lazy=True)
    earnings = db.relationship('Earning', backref='cultivation', lazy=True)

class Hall(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    max_cubes = db.Column(db.Integer)
    area = db.Column(db.Float)
    is_empty = db.Column(db.Boolean, default=True)
    cultivations = db.relationship('Cultivation', backref='hall', lazy=True)

class Harvest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cultivation_id = db.Column(db.Integer, db.ForeignKey('cultivation.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    ex = db.Column(db.Float)
    a = db.Column(db.Float)
    b = db.Column(db.Float)
    c = db.Column(db.Float)
    sr = db.Column(db.Float)
    pw = db.Column(db.Float)

class Cost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cultivation_id = db.Column(db.Integer, db.ForeignKey('cultivation.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    value = db.Column(db.Float, nullable=False)

class Earning(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cultivation_id = db.Column(db.Integer, db.ForeignKey('cultivation.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    value = db.Column(db.Float, nullable=False)


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

    halls = Hall.query.filter_by(user_id = session["user_id"]).all()
    nohalls = None
    if not halls:
        nohalls = True
    
    #status_list = ["przerastanie", "torf", "zbiory"]

    for cultivation in cultivations:
        match cultivation.status:
            case "przerastanie":
                cultivation.status0 = True
            case "torf":
                cultivation.status1 = True
            case "zbiory":
                cultivation.status2 = True
        
        
    return render_template("index.html", cultivations=cultivations, nohalls=nohalls)


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
    
    if request.method == "POST": 
        forms =["date", "hall_id", "manufacturer", "phase", "cubes_count", "price"]
        answ = {"user_id":session["user_id"]}

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
            price = answ["price"],
            status = "przerastanie"
        )
        db.session.add(cultivation)
        db.session.commit()
        
        cost = Cost(
            cultivation_id = db.session.query(Cultivation.id).filter_by(hall_id = answ["hall_id"]).scalar(),
            name = "Kostka",
            value = float(answ["price"]) * float(answ["cubes_count"])
        )
        db.session.add(cost)
        hall = Hall.query.get(answ["hall_id"])
        hall.is_empty = False
        db.session.commit()

        flash("Uprawa została stworzona")
        return redirect("/")

    else:
        date = datetime.now()
        halls = Hall.query.filter_by(user_id = session["user_id"]).all()
        return render_template("newcultivation.html",errors=errors, halls=halls, date = date.strftime("%Y-%m-%d"))

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

@app.route('/harvest/<int:cultivation_id>', methods=["GET", "POST"])
@login_required
def harvest(cultivation_id):

    if request.method == "POST":
        forms = ["ex", "a", "b", "c", "sr", "pw"]
        answ = {}

        for form in forms:
            if not request.form.get(form):
                answ[form] = 0.0
            else:
                answ[form] = request.form.get(form)
        date = request.form.get("date").replace("T", " ")

        harvest = Harvest(
            cultivation_id = cultivation_id,
            date = datetime.strptime(date, '%Y-%m-%d %H:%M'),
            ex = answ["ex"],
            a = answ["a"],
            b = answ["b"],
            c = answ["c"],
            sr = answ["sr"],
            pw = answ["pw"]
        )
        db.session.add(harvest)
        db.session.commit()
        
        flash("Zbiory zostały dodane")
        return redirect("/harvests")

    else:
        cultivation = Cultivation.query.filter_by(id = cultivation_id).first()
        date = datetime.now()
        return render_template('harvest.html', cultivation=cultivation, date=date.strftime("%Y-%m-%dT%H:%M"))

@app.route('/harvests')
@login_required
def harvests():
    
    query_results = (
    db.session.query(Cultivation,
                     db.func.sum(Harvest.ex).label("sum_ex"),
                     db.func.sum(Harvest.b).label("sum_a"),
                     db.func.sum(Harvest.b).label("sum_b"),
                     db.func.sum(Harvest.c).label("sum_c"),
                     db.func.sum(Harvest.sr).label("sum_sr"),
                     db.func.sum(Harvest.pw).label("sum_pw"))
    .join(Harvest)
    .filter(Cultivation.user_id == session["user_id"])
    .group_by(Cultivation.id)
    .all()
    )

    cultivations = []
    for cultivation, sum_ex, sum_a, sum_b, sum_c, sum_sr, sum_pw in query_results:
        cultivation.sum_ex = sum_ex
        cultivation.sum_a = sum_a
        cultivation.sum_b = sum_b
        cultivation.sum_c = sum_c
        cultivation.sum_sr = sum_sr
        cultivation.sum_pw = sum_pw
        cultivation.sum = sum_ex + sum_a + sum_b + sum_c + sum_sr + sum_pw
        cultivations.append(cultivation)

    return render_template("harvests.html", cultivations=cultivations)

@app.route('/peat/<int:cultivation_id>', methods=["GET", "POST"])
@login_required
def peat(cultivation_id):

    cultivation = Cultivation.query.filter_by(id = cultivation_id).first()

    if request.method == "POST":
        date = request.form.get("date")
        cultivation.peat_date = datetime.strptime(date, '%Y-%m-%d').date()
        cultivation.status = "torf"
        db.session.commit()

        flash("Dodano datę torfu:" + date)
        return redirect("/")
    else:
        date = datetime.now()
        return render_template('peat.html', cultivation=cultivation, date=date.strftime("%Y-%m-%d"))
            


@app.route('/shock/<int:cultivation_id>', methods=["GET", "POST"])
@login_required
def shock(cultivation_id):

    cultivation = Cultivation.query.filter_by(id = cultivation_id).first()

    if request.method == "POST":
        date = request.form.get("date").replace("T", " ")
        cultivation.shock_date = datetime.strptime(date, '%Y-%m-%d %H:%M')
        cultivation.status = "zbiory"
        db.session.commit()

        flash("Dodano datę szoku:" + date)
        return redirect("/")

    else:
        date = datetime.now()
        return render_template('shock.html', cultivation=cultivation, date=date.strftime("%Y-%m-%dT%H:%M"))


