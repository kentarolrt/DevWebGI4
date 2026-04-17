import flask
import utils
import flask_socketio

app = flask.Flask(__name__, static_url_path='/static')
app.teardown_appcontext(utils.closeDB)
app.secret_key = "secret1234"

socket = flask_socketio.SocketIO(app, async_mode='gevent')

@app.route('/') 
def home():
    
    return flask.render_template('home.html', user=flask.session.get('username'))
  
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if flask.request.method == 'POST':
        username = flask.request.form.get('username', '').strip()
        password = flask.request.form.get('password', '').strip()
        lastname = flask.request.form.get('lastname', '').strip()
        firstname = flask.request.form.get('firstname', '').strip()
        email = flask.request.form.get('email', '').strip()
        age = flask.request.form.get('age', '').strip()
        gender = flask.request.form.get('gender', '').strip()
        birthdate = flask.request.form.get('birthdate', '').strip()

        success, reason = utils.createUser(username, password, lastname, firstname, email, age, gender, birthdate)

        if success:
            flask.session['username'] = username
            return flask.redirect('/')
        else:
            return flask.redirect(f'/signup?error={reason}')
    else:
        return flask.render_template('signup.html', user=flask.session.get('username'))

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
        return flask.render_template('login.html', user=flask.session.get('username'))   
    
@app.route('/profile')
def profil():
    if 'username' not in flask.session:
        return flask.redirect('/login')

    user_data = utils.getUser(flask.session['username'])
    return flask.render_template('profile.html', user=flask.session.get('username'), user_data=user_data)

@app.route('/profile/update', methods=['POST'])
def profile_update():
    if 'username' not in flask.session:
        return flask.jsonify({'ok': False, 'error': 'not_logged_in'}), 401

    data = flask.request.get_json()
    field = data.get('field', '')
    value = data.get('value', '').strip()

    if not field or not value:
        return flask.jsonify({'ok': False, 'error': 'empty'})

    success, reason = utils.updateUser(flask.session['username'], field, value)

    if success:
        if field == 'username':
            flask.session['username'] = value
        return flask.jsonify({'ok': True})
    else:
        return flask.jsonify({'ok': False, 'error': reason})

@app.route('/logout')
def logout():
    flask.session.clear()
    return flask.redirect('/')


with app.app_context():
    utils.initDB()
    utils.createAdmin('admin', 'admin1234')

socket.run(app, port = 5500)