import flask

app = flask.Flask(__name__, static_folder = 'static', static_url_path = '/static')

@app.route('/')
def home():

    return flask.send_file('./static/html/index.html')

app.run(port = 5500)