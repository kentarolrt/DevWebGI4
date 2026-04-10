import flask

app = flask.Flask(__name__, static_folder = 'static', static_url_path = '/static')

@app.route('/')
def home():
    return flask.send_file('./static/html/index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():

    return flask.send_file('./static/html/signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    
    return flask.send_file('./static/html/login.html')

app.run(port = 5500)