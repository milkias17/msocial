import functools

from flask import (Blueprint, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        error = None

        for item in [username, password]:
            if not item:
                error = "Please fill out all required fields"

        if error:
            flash(error)
            return redirect(url_for("auth.login"))
        else:
            db = get_db()
            user = db.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
            if user is None:
                error = "Incorrect username."
            elif not check_password_hash(user["password"], password):
                error = "Incorrect password."

            if error is None:
                session.clear()
                session["user_id"] = user["id"]
                return redirect(url_for("index"))

            flash(error)
            return redirect(url_for("auth.login"))

    return render_template("login.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        f_name = request.form["fname"]
        l_name = request.form["lname"]
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        error = None

        for item in [f_name, l_name, username, email, password]:
            if not item:
                error = "Please fill out all required fields"

        if error:
            flash(error)
        else:
            db = get_db()
            password_hash = generate_password_hash(password)
            if db.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone():
                error = "Username already exists!"
                flash(error)
            elif db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone():
                error = "Email already in use!"
                flash(error)
            else:
                db.execute(
                    """
                        INSERT INTO users (f_name, l_name, username, password, email)
                        VALUES (?,?,?,?,?)
                        """,
                    (f_name, l_name, username, password_hash, email),
                )
                db.commit()
            return redirect(url_for("auth.login"))
    return render_template("register.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@bp.before_app_request
def load_logged_user():
    user_id = session.get("user_id")
    if user_id:
        g.user = (
            get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        )
    else:
        g.user = None


def login_required(view):
    @functools.wraps(view)
    def check_logged_in(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        else:
            return view(*args, **kwargs)

    return check_logged_in
