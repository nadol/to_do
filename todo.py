import os
import time
from sqlite3 import dbapi2 as sqlite3
from hashlib import md5
from datetime import datetime
from flask import Flask, request, session, url_for, redirect, \
     render_template, abort, g, flash, _app_ctx_stack
from werkzeug import check_password_hash, generate_password_hash

"""
ToDo - task management app - documentation
"""
__author__ =  'Mateusz Nadolski'
__version__=  '0.1'

# configuration
DATABASE = os.path.dirname(os.path.abspath(__file__)) + '/tmp/to_do.db'
DEBUG = True
SECRET_KEY = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

app = Flask(__name__)
app.config.from_object(__name__)

def get_db():
  """Opens a new database connection if there is none yet for the
  current application context.
  """
  top = _app_ctx_stack.top
  if not hasattr(top, 'sqlite_db'):
    top.sqlite_db = sqlite3.connect(app.config['DATABASE'])
    top.sqlite_db.row_factory = sqlite3.Row
  return top.sqlite_db

def get_user_id(email):
    """Convenience method to look up the id for a email"""
    rv = query_db('select user_id from user where email = ?',
                  [email], one=True)
    return rv[0] if rv else None

@app.before_request
def before_request():
  g.user = None
  if 'user_id' in session:
    g.user = query_db('select * from user where user_id = ?', [session['user_id']], one=True)


@app.teardown_appcontext
def close_database(exception):
  """Closes the database again at the end of the request."""
  top = _app_ctx_stack.top
  if hasattr(top, 'sqlite_db'):
    top.sqlite_db.close()

def query_db(query, args=(), one=False):
  """Queries the database and returns a list of dictionaries."""
  cur = get_db().execute(query, args)
  rv = cur.fetchall()
  return (rv[0] if rv else None) if one else rv


@app.errorhandler(404)
def page_not_found(e):
  """Controller handling the 404 error"""
  return render_template('404.html'), 404

@app.route('/')
@app.route('/index')
def index():
  """Controller handling the main page request"""
  return render_template('index.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
  """Logs the user in."""
  if g.user:
    return redirect(url_for('index'))
  error = None
  if request.method == 'POST':
    user = query_db('''select * from user where
        email = ?''', [request.form['email']], one=True)
    if user is None:
        error = 'Invalid email'
    elif not check_password_hash(user['pw_hash'],
                                 request.form['password']):
      error = 'Invalid password'
    else:
      flash('You were logged in')
      session['user_id'] = user['user_id']
      return redirect(url_for('index'))
  return render_template('signin.html', error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
  """Registers the user."""
  if g.user:
    return redirect(url_for('index'))
  error = None
  if request.method == 'POST':
    if not request.form['first_name']:
      error = 'You have to enter your first name'
    elif not request.form['last_name']:
      error = 'You have to enter your last name'
    elif not request.form['email'] or '@' not in request.form['email']:
      error = 'You have to enter a valid email address'
    elif not request.form['password']:
      error = 'You have to enter a password'
    elif request.form['password'] != request.form['password_confirmation']:
      error = 'Entered password do not match'
    elif get_user_id(request.form['email']) is not None:
      error = 'Entered email address is already in use'
    else:
      db = get_db()
      db.execute('''insert into user (
        first_name, last_name, email, pw_hash) values (?, ?, ?, ?)''',
        [request.form['first_name'], request.form['last_name'], request.form['email'],
         generate_password_hash(request.form['password'])])
      db.commit()
      flash('You were successfully registered and can login now')
      return redirect(url_for('signin'))
  return render_template('signup.html', error=error)

@app.route('/signout', methods=['GET'])
def signout():
  """Logs the user out."""
  return render_template('signout.html')

if __name__ == '__main__':
  app.run()