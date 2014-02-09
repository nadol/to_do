from flask import Flask, render_template

"""
ToDo - task management app - documentation
"""
__author__ =  'Mateusz Nadolski'
__version__=  '0.1'

app = Flask(__name__)

@app.errorhandler(404)
def page_not_found(e):
    """ Controller handling the 404 error """
    return render_template('404.html'), 404

@app.route('/')
@app.route('/index')
def index():
  """ Controller handling the main page request """
  return render_template('index.html')