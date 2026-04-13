import flask
import utils
import flask_socketio

app = flask.Flask(__name__, static_url_path='/static')
app.teardown_appcontext(utils.closeDB)

socket = flask_socketio.SocketIO(app, async_mode='gevent')

@app.route('/')
def home():

    return flask.send_file('static/html/home.html')
  
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if flask.request.method == 'POST':
        username = flask.request.form.get('username', '').strip()
        password = flask.request.form.get('password', '').strip()

        success, reason = utils.createUser(username, password)

        if success:
            return flask.redirect('/')
        else :
            return flask.redirect(f'/signup?error{reason}')
    else:
        return flask.send_file('static/html/signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if flask.request.method == 'POST':
        return flask.redirect('/')
    else:
        return flask.send_file('static/html/login.html')    

with app.app_context():
    utils.initDB()
    utils.createAdmin('admin', 'admin1234')

socket.run(app, port = 5500)