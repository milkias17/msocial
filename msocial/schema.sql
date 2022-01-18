DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS posts;
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  f_name TEXT NOT NULL,
  l_name TEXT NOT NULL,
  username TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  profile_pic TEXT DEFAULT 'files/profile-pics/default-profile-pic.jpg',
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  body TEXT NOT NULL,
  author_id INT NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (author_id) REFERENCES users (id)
);
CREATE TABLE followers (
  follower_id INTEGER NOT NULL,
  followed_id INTEGER NOT NULL,
  FOREIGN KEY (follower_id) REFERENCES users(id),
  FOREIGN KEY (followed_id) REFERENCES users(id)
);

