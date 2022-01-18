from flask import (Blueprint, flash, g, redirect, render_template, request,
                   url_for)

from .auth import login_required
from .db import get_db

posts_bp = Blueprint("posts", __name__)


@posts_bp.route("/create", methods=["POST"])
@login_required
def create_post():
    user = g.user
    body = request.form["body"]
    author_id = user["id"]

    if not body:
        flash("Fill in what you want to post first!")
        return redirect(url_for("posts.create_post"))
    db = get_db()
    db.execute("INSERT INTO posts (body, author_id) VALUES (?,?)", (body, author_id))
    db.commit()

    return redirect(url_for("index"))
