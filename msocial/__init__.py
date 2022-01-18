import os

from flask import Flask, flash, g, redirect, render_template, url_for

app = Flask(__name__)
app.config["DATABASE"] = os.path.join(app.instance_path, "msocial.sqlite")
app.config["SECRET_KEY"] = "dev"
app.config["UPLOAD_FOLDER"] = "msocial/static/files/profile-pics/"
if os.getenv("SECRET_KEY"):
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
else:
    app.config["SECRET_KEY"] = "dev"

try:
    os.makedirs(app.instance_path)
except OSError:
    pass

from . import db
from .auth import bp, login_required
from .posts import posts_bp
from .user import user_bp

app.register_blueprint(bp)
app.register_blueprint(posts_bp)
app.register_blueprint(user_bp)


@app.route("/")
@login_required
def index():
    cur_db = db.get_db()
    posts = cur_db.execute(
        """
        SELECT
        body,
        f_name || ' ' || l_name AS author,
        username,
        profile_pic,
        posts.created,
        STRFTIME('%H:%M %m,%Y', posts.created) AS prettyCreated
        FROM
        posts
        JOIN users ON posts.author_id = users.id
        JOIN followers ON followed_id = users.id
        WHERE
        follower_id = ?
        UNION
        SELECT
        body,
        f_name || ' ' || l_name AS author,
        username,
        profile_pic,
        posts.created,
        STRFTIME('%H:%M %m,%Y', posts.created) AS prettyCreated
        FROM posts
        JOIN users ON posts.author_id = users.id
        WHERE author_id = ?
        ORDER BY posts.created DESC
        ;
            """,
        (g.user["id"], g.user["id"]),
    ).fetchall()
    return render_template("home.html", posts=posts, id=g.user["id"])


@app.route("/explore")
@login_required
def explore():
    cur_db = db.get_db()
    posts = cur_db.execute(
        "SELECT body, f_name || ' ' || l_name AS author,"
        "username, profile_pic, STRFTIME('%H:%M %m,%Y', posts.created) AS created FROM posts JOIN users ON posts.author_id = users.id ORDER BY posts.created DESC"
    ).fetchall()
    return render_template("home.html", posts=posts, id=g.user["id"])
