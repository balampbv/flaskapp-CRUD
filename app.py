from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
# from data import Articles
from flask.ext.pymongo import PyMongo
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from datetime import datetime
from bson.objectid import ObjectId


app = Flask(__name__)

# connect to MongoDB with the defaults
app.config['MONGO_DBNAME'] = 'flasklogin'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/flasklogin'


mongo = PyMongo(app)


# Articles = Articles()


# index
@app.route('/')
def index():
    return render_template('home.html')

# About


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/articles')
def articles():
    artic = mongo.db.articles
    articles = []
    for article in artic.find():
        articles.append({'id': article['_id'], 'title': article[
                        'title'], 'author': article['author'], 'date': article['date']})
        app.logger.info(articles)
    return render_template('articles.html', articles=articles)


@app.route('/articles/<string:id>/')
def article(id):
    articles = mongo.db.articles
    article = articles.find_one({'_id': ObjectId(id)})
    app.logger.info(article)
    return render_template('article.html', article=article)


class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message="Passwords do not match")

    ])
    confirm = PasswordField('Confirm Password')


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        users = mongo.db.users
        name = form.name.data
        email = form.email.data
        username = form.username.data
        hashpass = sha256_crypt.encrypt(str(form.password.data))

        # Execute query
        users.insert({'name': request.form['name'], 'username': request.form[
                     'username'], 'email': request.form['email'], 'password': hashpass})

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# USer Login


@app.route('/login', methods=['GET', 'POST'])
def login():
    users = mongo.db.users
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']
        login_user = users.find_one({'username': request.form['username']})
        if login_user:
            if sha256_crypt.verify(password_candidate, login_user['password']):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now in logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Password Do not match'
                return render_template('login.html', error=error)

        else:
            error = 'Username not found'
            return render_template('login.html', error=error)
    return render_template('login.html')

# Check if user logged in


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized Please Login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Dashboard


@app.route('/dashboard')
@is_logged_in
def dashboard():
    artic = mongo.db.articles
    articles = []
    for article in artic.find():
        articles.append({'id': article['_id'], 'title': article[
                        'title'], 'author': article['author'], 'date': article['date']})
        app.logger.info(articles)
    if articles:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No articles found'
        return render_template('dashboard.html', msg=msg)
# else:
    #	msg = 'No Articles found'
    #	return render_template('dashboard.html',msg=msg)


# Articale Form class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=100)])
    body = TextAreaField('body', [validators.Length(min=30)])


# Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        articles = mongo .db.articles
        title = form.title.data
        body = form.body.data

        # Execute
        articles.insert({'title': request.form['title'], 'body': request.form[
                        'body'], 'author': session['username'], 'date': datetime.now()})

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)


# eDIT Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    articles = mongo.db.articles
    # Get article by ID
    article = articles.find_one({'_id': ObjectId(id)})
    # Get form
    form = ArticleForm(request.form)
    # Populate article from fiels
    form.title.data = article['title']
    form.body.data = article['body']
    if request.method == 'POST' and form.validate():
        articles = mongo .db.articles
    	title = form.title.data
    	body = form.body.data

    # Execute
    	articles.update_one({'_id': ObjectId(id)}, {'$set': {'title': request.form[
                        'title'], 'body': request.form['body'], 'author': session['username'], 'date': datetime.now()}})

    	flash('Article Updated', 'success')

    	return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)


# Delete Article
@app.route('/delete_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def delete_article(id):
    articles = mongo.db.articles
    # Get article by ID
    article = articles.delete_many({'_id': ObjectId(id)})
    flash('Article Deleted','success')
    return redirect(url_for('dashboard'))


# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are logged out', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)
