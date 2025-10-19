from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.sqlite3"
app.config["SECRET_KEY"] = "CosmoTheSigma75757"
db = SQLAlchemy(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(67))
    email = db.Column(db.String(67), unique=True)
    password = db.Column(db.String(67))
    ideas = db.relationship("Ideas", backref="user", lazy=True)
    likes = db.relationship("Likes", backref="user", lazy=True)

class Ideas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    likes = db.relationship("Likes", backref="idea", lazy=True)

class Likes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    idea_id = db.Column(db.Integer, db.ForeignKey('ideas.id'))

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('home.html', user=session.get("user"))

@app.route('/ideahub')
def ideahub():
    if "user" not in session:
        return redirect(url_for('home'))

    ideas = Ideas.query.order_by(Ideas.timestamp.desc()).all()
    current_user = Users.query.filter_by(fullname=session["user"]).first()

    liked_idea_ids = [like.idea_id for like in current_user.likes]
    return render_template("IdeaHub.html", user=session["user"], ideas=ideas, liked_idea_ids=liked_idea_ids)

@app.route('/signup', methods=["POST"])
def signup():
    fullname = request.form.get("fullname")
    email = request.form.get("email")
    password = request.form.get("password")

    if not fullname or not email or not password:
        return redirect(url_for('home'))

    existing_user = Users.query.filter_by(email=email).first()
    if existing_user:
        return redirect(url_for('home'))

    new_user = Users(fullname=fullname, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()

    session["user"] = fullname
    return redirect(url_for('ideahub'))

@app.route('/login', methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    user = Users.query.filter_by(email=email, password=password).first()
    if user:
        session["user"] = user.fullname
        return redirect(url_for('ideahub'))
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for('home'))

@app.route('/post_idea', methods=["POST"])
def post_idea():
    if "user" not in session:
        return redirect(url_for('home'))

    title = request.form.get("title")
    description = request.form.get("description")
    if not title or not description:
        return redirect(url_for('ideahub'))

    user = Users.query.filter_by(fullname=session["user"]).first()
    new_idea = Ideas(title=title, description=description, user=user)
    db.session.add(new_idea)
    db.session.commit()

    return redirect(url_for('ideahub'))

@app.route('/delete_idea/<int:idea_id>', methods=["POST"])
def delete_idea(idea_id):
    if "user" not in session:
        return redirect(url_for('home'))

    idea = Ideas.query.get_or_404(idea_id)
    if idea.user.fullname != session["user"]:
        return redirect(url_for('ideahub'))

    db.session.delete(idea)
    db.session.commit()
    return redirect(url_for('ideahub'))

@app.route('/like/<int:idea_id>', methods=["POST"])
def like_idea(idea_id):
    if "user" not in session:
        return redirect(url_for('home'))

    user = Users.query.filter_by(fullname=session["user"]).first()
    idea = Ideas.query.get_or_404(idea_id)

    existing_like = Likes.query.filter_by(user_id=user.id, idea_id=idea.id).first()

    if existing_like:
        db.session.delete(existing_like)
    else:
        new_like = Likes(user=user, idea=idea)
        db.session.add(new_like)

    db.session.commit()
    return redirect(url_for('ideahub'))

if __name__ == '__main__':
    app.run(debug=True)
