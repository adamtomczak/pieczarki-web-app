from flask import redirect, session, flash
from functools import wraps


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function



def pln(value):
    """Format value as PLN."""
    return f"{value:,.2f}zł"

def isPasswordStrong(password):
    def contain_number(password):
        for n in range(len(password)):
            if password[n].isnumeric():
                return True
        return False

    def contain_uppercase(password):
        for n in range(len(password)):
            if password[n].isupper():
                return True
        return False

    if len(password) < 8:
        flash("Hasło musi mieć co najmiej 8 znaków.")
        return False
    if not contain_number(password):
        flash("Hasło musi zawierać co najmiej jedną cyfrę.")
        return False
    if not contain_uppercase(password):
        flash("Hasło musi zawierać do najmniej jedną wielką literę.")
        return False
    
    return True