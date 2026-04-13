import flask
import utils
import flask_socketio

app = flask.Flask(__name__, static_url_path='/static')
app.teardown_appcontext(utils.closeDB)
app.secret_key = "secret1234"

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
            flask.session['username'] = username
            return flask.redirect('/')
        else:
            return flask.redirect(f'/signup?error={reason}')
    else:
        return flask.send_file('static/html/signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if flask.request.method == 'POST':
        username = flask.request.form.get('username', '').strip()
        password = flask.request.form.get('password', '').strip()

        if not username or not password :
            return flask.redirect('/login?error=empty')

        success, reason = utils.loginUser(username, password)

        if success:
            flask.session['username'] = username
            return flask.redirect('/')
        else:
            return flask.redirect(f'/login?error={reason}')        
    else:
        return flask.send_file('static/html/login.html')    

@app.route('/logout')
def logout():
    flask.session.clear()
    return flask.redirect('/login')


with app.app_context():
    utils.initDB()
    utils.createAdmin('admin', 'admin1234')

socket.run(app, port = 5500)