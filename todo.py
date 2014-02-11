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
    rv = query_db('SELECT id FROM user WHERE email = ?',
                  [email], one=True)
    return rv[0] if rv else None

@app.before_request
def before_request():
  g.user = None
  if 'id' in session:
    g.user = query_db('SELECT * FROM user WHERE id = ?', [session['id']], one=True)


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
  if g.user:
    return redirect(url_for('projects_list'))
  return render_template('index.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
  """Logs the user in."""
  if g.user:
    return redirect(url_for('projects_list'))
  error = None
  if request.method == 'POST':
    user = query_db('''SELECT * FROM user WHERE
        email = ?''', [request.form['email']], one=True)
    if user is None:
        error = 'Invalid email'
    elif not check_password_hash(user['pw_hash'],
                                 request.form['password']):
      error = 'Invalid password'
    else:
      session['id'] = user['id']
      return redirect(url_for('projects_list'))
  return render_template('signin.html', error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
  """Registers the user."""
  if g.user:
    return redirect(url_for('projects_list'))
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

@app.route('/signout')
def signout():
  """Logs the user out."""
  flash('You were logged out')
  session.pop('id', None)
  return redirect(url_for('index'))

@app.route('/projects_list')
def projects_list():
  """Shows the user's projects with information about
     done tasks, all tasks and overall progress.
  """
  projects = query_db('SELECT * FROM project WHERE user_id = ?', [session['id']])
  stats = {}
  for project in projects:
    done_tasks = len(query_db('SELECT * FROM task WHERE project_id = ? and status = 1', [project['id']]))
    all_tasks = len(query_db('SELECT * FROM task WHERE project_id = ?', [project['id']]))
    if all_tasks != 0:
      progress = done_tasks / float(all_tasks) * 100
    else:
      progress = 0
    info = (done_tasks, all_tasks, progress)
    stats[project['id']] = info
  return render_template('projects_list.html', projects=projects, stats=stats)

@app.route('/add_project', methods=['GET', 'POST'])
def add_project():
  """Adds the new project"""
  error = None
  if request.method == 'POST':
    if not request.form['name']:
      error = 'You have to enter the project title'
    else:
      db = get_db()
      db.execute('''insert into project (
        user_id, name, description, status) values (?, ?, ?, ?)''',
        [session['id'], request.form['name'], request.form['description'], 0])
      db.commit()
      return redirect(url_for('projects_list'))
  return render_template('add_project.html', error=error)

@app.route('/<project_id>/show')
def show_project(project_id):
  """Shows the current project tasks"""
  tasks = query_db('SELECT * FROM task WHERE project_id = ? and status = 0', [project_id])
  done = query_db('SELECT * FROM task WHERE project_id = ? and status = 1', [project_id])
  return render_template('project_show.html', project_id=project_id, tasks=tasks, done=done)

@app.route('/<project_id>/delete')
def delete_project(project_id):
  """Deletes the project"""
  db = get_db()
  db.execute("DELETE FROM project WHERE id =%i" %(int(project_id)))
  db.commit()
  return redirect(url_for('projects_list'))

@app.route('/<project_id>/add_task', methods=['GET', 'POST'])
def add_task(project_id):
  """Adds the new task to current project"""
  error = None
  if request.method == 'POST':
    if not request.form['name']:
      error = 'You have to enter the task description'
    else:
      db = get_db()
      db.execute('''insert into task (
        project_id, name, status) values (?, ?, ?)''',
        [project_id, request.form['name'], 0])
      db.commit()
      return redirect(url_for('show_project', project_id=project_id))
  return render_template('add_task.html', error=error)

@app.route('/<project_id>/<task_id>/edit_task', methods=['GET', 'POST'])
def edit_task(project_id, task_id):
  """Edits the task"""
  error = None
  if request.method == 'POST':
    if not request.form['name']:
      error = 'You have to enter the task description'
    else:
      db = get_db()
      db.execute("UPDATE task SET name= ? WHERE id = ?", [str(request.form['name']), int(task_id)])
      db.commit()
      return redirect(url_for('show_project', project_id=project_id))
  return render_template('edit_task.html', error=error)

@app.route('/<project_id>/<task_id>/check_task')
def check_task(project_id, task_id):
  """Checks off the task"""
  db = get_db()
  db.execute("UPDATE task SET status=1 WHERE id =%i" %(int(task_id)))
  db.commit()
  return redirect(url_for('show_project', project_id=project_id))

@app.route('/<project_id>/<task_id>/delete_task')
def delete_task(project_id, task_id):
  """Deletes the task"""
  db = get_db()
  db.execute("DELETE FROM task WHERE id =%i" %(int(task_id)))
  db.commit()
  return redirect(url_for('show_project', project_id=project_id))

if __name__ == '__main__':
  app.run()