import flask
from flask import url_for

app = flask.Flask(__name__, static_folder = 'static', static_url_path = '/static')

@app.route('/')
def home():
    a = url_for('static', filename='html')
    return flask.send_file('./static/html/index.html')

@app.post('/signup')
def signup():

    return flask.send_file('./static/html/signup.html')

app.run(port = 5500)