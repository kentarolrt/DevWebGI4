import flask
import utils
import flask_socketio

app = flask.Flask(__name__, static_url_path='/static')
app.teardown_appcontext(utils.closeDB)

socket = flask_socketio.SocketIO(app, async_mode='gevent')

@app.route('/')
def home():

    return flask.send_file('static/html/home.html')
  
@app.route('/signup', methods=['POST'])
def signup():

    return flask.send_file('static/html/home.html')

@app.route('/login', methods=['POST'])
def login():
    
    return flask.send_file('static/html/home.html')

with app.app_context():
    utils.initDB()

socket.run(app, port = 5500)