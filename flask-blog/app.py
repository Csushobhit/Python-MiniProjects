from flask import Flask, render_template, request, flash, redirect, url_for, session, g
from config import Config
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from functools import wraps


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', back_populates='author')

    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), index=True)
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', back_populates='posts')

    comments = db.relationship('Comment', back_populates='post', lazy='dynamic', cascade="all, delete-orphan")
    

    def __repr__(self):
        return f'<Post {self.title}>'

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    author_name = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    post = db.relationship('Post', back_populates='comments')

    def __repr__(self):
        return f'<Comment {self.content[:30]}...>'

@app.cli.command('create-admin')
def create_admin():
    username = input('Enter admin username: ')
    if User.query.filter_by(username=username).first():
        print(f'Error: User with username {username} already exists.')
        return
    password = input('Enter admin password: ')

    new_admin = User(username=username)
    new_admin.set_password(password)
    db.session.add(new_admin)
    db.session.commit()
    print(f'Admin user {username} created successfully!')
    


@app.route('/login', methods=['GET', 'POST'])
def home():
    return "Hello, World!"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash('Invalid username or password. Please try again.')
            return redirect(url_for('login'))
        session['user_id'] = user.id
        flash('You have been successfully logged in!')
        return redirect(url_for('home'))
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been successfully logged out.')
    return redirect(url_for('home'))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to be logged in to access this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(int(user_id))

@app.route('/admin')
def admin_dashboard():
    return f"<h1>Welcome to the Admin Dashboard, {g.user.username}!</h1>"
