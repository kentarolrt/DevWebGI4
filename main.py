import flask

app = flask.Flask(__name__, static_url_path='/static')

@app.route('/')
def home():

    return flask.send_file('static/html/home.html')
  
@app.route('/signup', methods=['POST'])
def signup():

    return flask.send_file('static/html/home.html')

@app.route('/login', methods=['POST'])
def login():
    
    return flask.send_file('static/html/home.html')

app.run(port = 5500)