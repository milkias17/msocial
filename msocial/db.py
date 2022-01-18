import sqlite3

import click
from flask import g
from flask.cli import with_appcontext

from . import app


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()

    with app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))


def get_user(username):
    db = get_db()
    return db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def get_num_following(user):
    db = get_db()
    return db.execute(
        """
            SELECT
            IIF(
                EXISTS(
                    SELECT
                    *
                    FROM
                    followers
                    WHERE
                    follower_id = ?
                    ),
                (
                    SELECT
                    COUNT(followed_id)
                    FROM
                    followers
                    WHERE
                    follower_id = ?
                    ),
                0
                ) following;
            """,
        (user["id"], user["id"]),
    ).fetchone()["following"]


def get_num_followers(user):
    db = get_db()
    return db.execute(
        """
        SELECT
        IIF(
            EXISTS(
                SELECT
                *
                FROM
                followers
                WHERE
                followed_id = ?
                ),
            (
                SELECT
                COUNT(follower_id)
                FROM
                followers
                WHERE
                followed_id = ?
                ),
            0
            ) followers;
        """,
        (user["id"], user["id"]),
    ).fetchone()["followers"]


def get_posts(user):
    db = get_db()
    return db.execute(
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
        (user["id"],),
    ).fetchall()


def get_num_posts(user):
    db = get_db()
    return db.execute(
        """
        SELECT
        IIF(
            EXISTS(
                SELECT
                *
                FROM
                posts
                WHERE
                author_id = ?
                ),
            (
                SELECT
                COUNT(body)
                FROM
                posts
                WHERE
                author_id = ?
                ),
            0
            ) num_posts;
            """,
        (user["id"], user["id"]),
    ).fetchone()["num_posts"]


def get_followers(user):
    db = get_db()
    return db.execute(
        "SELECT username, profile_pic FROM followers JOIN users ON follower_id = users.id WHERE followed_id = ?",
        (user["id"],),
    ).fetchall()


def get_following(user):
    db = get_db()
    return db.execute(
        "SELECT username, profile_pic FROM followers JOIN users ON followed_id = users.id WHERE follower_id = ?",
        (user["id"],),
    ).fetchall()


def is_following(user1, user2):
    db = get_db()
    tmp = db.execute(
        "SELECT * FROM followers WHERE follower_id = ? AND followed_id = ?",
        (user1["id"], user2["id"]),
    ).fetchall()
    return len(tmp) > 0


def is_different(username, field, new_value):
    user = get_user(username)
    return user[field] != new_value


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo("Initialized the database")


app.teardown_appcontext(close_db)
app.cli.add_command(init_db_command)
