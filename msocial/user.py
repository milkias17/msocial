import os

from flask import (Blueprint, flash, g, redirect, render_template, request,
                   url_for)

from . import app
from .auth import login_required
from .db import (get_db, get_followers, get_following, get_num_followers,
                 get_num_following, get_num_posts, get_user, is_different,
                 is_following)

user_bp = Blueprint("user_bp", __name__)


@user_bp.route("/follow/<username>")
@login_required
def follow(username):
    cur_db = get_db()
    user = g.user
    followed = get_user(username)
    if not followed:
        flash(f"User {username} doesn't exist")
        return redirect(url_for("index"))
    if followed["id"] == user["id"]:
        flash("You can't follow yourself!")
        return redirect(url_for("index"))

    cur_db.execute("INSERT INTO followers VALUES (?,?)", (user["id"], followed["id"]))
    cur_db.commit()
    return redirect(url_for("index"))


@user_bp.route("/unfollow/<username>")
@login_required
def unfollow(username):
    cur_db = get_db()
    cur_user = g.user
    target_user = get_user(username)
    if not target_user:
        flash(f"User {username} doesn't exist")
        return redirect(url_for("index"))
    if target_user["id"] == cur_user["id"]:
        flash("You cant unfollow yourself!")
        return redirect(url_for("index"))

    cur_db.execute(
        "DELETE FROM followers WHERE follower_id = ? AND followed_id = ?",
        (cur_user["id"], target_user["id"]),
    )
    cur_db.commit()
    return redirect(url_for("index"))


@user_bp.route("/profile/<username>")
def profile(username):
    cur_db = get_db()
    target_user = get_user(username)
    num_following = get_num_following(target_user)
    num_followers = get_num_followers(target_user)
    posts = cur_db.execute(
        """
            SELECT
            body,
            f_name || ' ' || l_name AS author,
            STRFTIME('%H:%M %m,%Y', posts.created) AS created
            FROM
            posts
            JOIN users ON posts.author_id = users.id
            WHERE
            users.id = ?
            ORDER BY posts.created DESC
            ;
            """,
        (target_user["id"],),
    ).fetchall()

    num_posts = get_num_posts(target_user)
    if g.user != target_user:
        return render_template(
            "profile_page.html",
            user=target_user,
            followers=num_followers,
            following=num_following,
            posts=posts,
            num_posts=num_posts,
            is_following=is_following(g.user, target_user),
        )
    else:
        return render_template(
            "profile_page.html",
            user=target_user,
            followers=num_followers,
            following=num_following,
            posts=posts,
            num_posts=num_posts,
        )


@user_bp.route("/profile/<username>/followers")
def user_followers(username):
    user = get_user(username)
    followers = get_followers(user)
    return render_template("followers.html", followers=followers, title="Followers")


@user_bp.route("/profile/<username>/following")
def user_following(username):
    user = get_user(username)
    following = get_following(user)
    return render_template("followers.html", followers=following, title="Following")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in [
        "jpeg",
        "jpg",
        "png",
    ]


def delete_if_exists(user_id):
    path = app.config["UPLOAD_FOLDER"]
    for file in os.listdir(path):
        if file.split(".", 1)[0] == str(user_id):
            os.remove(f"{path}/{file}")
            break


@user_bp.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        f_name = request.form["fname"]
        l_name = request.form["lname"]
        profile_image = request.files["profile_pic"]
        username = request.form["username"]
        email = request.form["email"]

        for item in [f_name, l_name, username, email]:
            if not item:
                flash("Please fill out all required fields")
                return redirect(url_for("user_bp.edit_profile"))

        cur_db = get_db()
        tmp = cur_db.execute(
            "SELECT * FROM users WHERE id!=? AND (username=? OR email=?)",
            (g.user["id"], username, email),
        ).fetchall()
        if tmp:
            flash("Username/email already in use")
            return redirect(url_for("user_bp.edit_profile"))

        if profile_image.filename != "":
            if profile_image and allowed_file(profile_image.filename):
                extension = profile_image.filename.rsplit(".", 1)[1].lower()
                filename = f'{g.user["id"]}.{extension}'
                save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                delete_if_exists(g.user["id"])
                profile_image.save(save_path)
                cur_db.execute(
                    "UPDATE users SET f_name = ?, l_name = ?, profile_pic = ?, username = ?, email = ? WHERE id = ?",
                    (
                        f_name,
                        l_name,
                        save_path.split("/", 2)[-1],
                        username,
                        email,
                        g.user["id"],
                    ),
                )
                cur_db.commit()
                return redirect(url_for("index"))
            else:
                flash("Problem with Uploaded Profile Image")
                return redirect(url_for("user_bp.edit_profile"))
        else:
            cur_db.execute(
                "UPDATE users SET f_name=?, l_name=?, username=?, email=?",
                (f_name, l_name, username, email),
            )
            cur_db.commit()
            return redirect(url_for("index"))

    return render_template("edit_profile.html")
