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
        username  = flask.request.form.get('username', '').strip()
        password  = flask.request.form.get('password', '').strip()
        lastname  = flask.request.form.get('lastname', '').strip()
        firstname = flask.request.form.get('firstname', '').strip()
        email     = flask.request.form.get('email', '').strip()
        age       = flask.request.form.get('age', '').strip()
        gender    = flask.request.form.get('gender', '').strip()
        birthdate = flask.request.form.get('birthdate', '').strip()

        member_type = flask.request.form.get('member_type', 'fils').strip()
        success, reason = utils.createUser(username, password, lastname, firstname, email, age, gender, birthdate, member_type)

        if success:
            flask.session['username'] = username
            return flask.redirect('/dashboard')
        else:
            return flask.redirect(f'/signup?error={reason}')
    else:
        return flask.render_template('signup.html', user=flask.session.get('username'))

@app.route('/login', methods=['GET','POST'])
def login():
    if flask.request.method == 'POST':
        username = flask.request.form.get('username', '').strip()
        password = flask.request.form.get('password', '').strip()

        if not username or not password:
            return flask.redirect('/login?error=empty')

        success, reason = utils.loginUser(username, password)

        if success:
            flask.session['username'] = username
            utils.recordConnection(username)
            return flask.redirect('/dashboard')
        else:
            return flask.redirect(f'/login?error={reason}')
    else:
        return flask.render_template('login.html', user=flask.session.get('username'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in flask.session:
        return flask.redirect('/login')

    user_data   = utils.getUser(flask.session['username'])
    connections = utils.getConnectionCount(flask.session['username'])
    devices     = utils.searchDevices('', '', '')

    total    = len(devices)
    active   = sum(1 for o in devices if o['status'] == 'actif')
    inactive = total - active
    nb_types = len(set(o['type'] for o in devices))

    resp = flask.make_response(flask.render_template(
        'dashboard.html',
        user=flask.session.get('username'),
        user_data=user_data,
        connections=connections,
        devices=devices,
        stats={'total': total, 'active': active, 'inactive': inactive, 'types': nb_types}
    ))
    resp.headers['Cache-Control'] = 'no-store'
    return resp

@app.route('/api/level-up', methods=['POST'])
def api_level_up():
    if 'username' not in flask.session:
        return flask.jsonify({'ok': False})
    success, result = utils.upgradeLevel(flask.session['username'])
    if success:
        user_data = utils.getUser(flask.session['username'])
        socket.emit('points_update', {
            'points': float(user_data['points']),
            'level': result
        }, room=flask.session['username'])
        return flask.jsonify({'ok': True, 'level': result})
    return flask.jsonify({'ok': False, 'error': result})

@app.route('/api/points')
def api_points():
    if 'username' not in flask.session:
        return flask.jsonify({'ok': False})
    user_data = utils.getUser(flask.session['username'])
    return flask.jsonify({'ok': True, 'points': float(user_data['points']), 'level': user_data['level']})

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

    data  = flask.request.get_json()
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

@app.route('/profile/delete', methods=['POST'])
def profile_delete():
    if 'username' not in flask.session:
        return flask.redirect('/login')
    username = flask.session.get('username')
    utils.deleteUser(username)
    flask.session.clear()
    return flask.redirect('/')

@app.route('/logout')
def logout():
    flask.session.clear()
    return flask.redirect('/')

@app.route('/search')
def search():
    query       = flask.request.args.get('q', '').strip()
    filter_type = flask.request.args.get('type', '').strip()
    filter_status = flask.request.args.get('status', '').strip()

    searched  = bool(query or filter_type or filter_status)
    results   = utils.searchDevices(query, filter_type, filter_status) if searched else None
    types     = utils.getTypes()

    return flask.render_template(
        'search.html',
        user=flask.session.get('username'),
        results=results,
        types=types,
        query=query,
        filter_type=filter_type,
        filter_status=filter_status,
        searched=searched
    )

@app.route('/members')
def membres():
    if 'username' not in flask.session:
        return flask.redirect('/login')
    all_members = utils.getAllMembers()
    return flask.render_template('membres.html', user=flask.session.get('username'), members=all_members)

@app.route('/member/<username>')
def profil_public(username):
    if 'username' not in flask.session:
        return flask.redirect('/login')
    member = utils.getUser(username)
    if not member:
        flask.abort(404)
    viewer = flask.session.get('username')
    is_owner = (viewer == username)
    is_admin = utils.getUser(viewer)['role'] == 'admin' if viewer else False
    return flask.render_template(
        'public_profile.html',
        user=viewer,
        member=member,
        is_owner=is_owner,
        is_admin=is_admin
    )

@app.route('/admin/delete/<username>', methods=['POST'])
def admin_delete_user(username):
    if 'username' not in flask.session:
        return flask.redirect('/login')
    viewer = flask.session.get('username')
    viewer_data = utils.getUser(viewer)
    if not viewer_data or viewer_data['role'] != 'admin':
        flask.abort(403)
    if viewer == username:
        flask.abort(403)
    success, _ = utils.deleteUser(username)
    if not success:
        flask.abort(400)
    return flask.redirect('/members')

@app.route('/device/<int:device_id>')
def device_detail(device_id):
    device = utils.getDevice(device_id)
    if not device:
        flask.abort(404)
    return flask.render_template('objet.html', user=flask.session.get('username'), device=device)

@app.route('/api/consult/<int:device_id>', methods=['POST'])
def api_consult(device_id):
    if 'username' not in flask.session:
        return flask.jsonify({'ok': False})
    device = utils.getDevice(device_id)
    if not device:
        return flask.jsonify({'ok': False})
    utils.addPoints(flask.session['username'], 0.50)
    user_data  = utils.getUser(flask.session['username'])
    new_points = float(user_data['points'])
    socket.emit('points_update', {
        'points': new_points,
        'level': user_data['level']
    }, room=flask.session['username'])
    return flask.jsonify({'ok': True, 'points': new_points, 'level': user_data['level']})

@socket.on('join')
def on_join():
    if 'username' in flask.session:
        flask_socketio.join_room(flask.session['username'])

@app.context_processor
def inject_types():
    try:
        return {'types': utils.getTypes()}
    except:
        return {'types': []}

with app.app_context():
    utils.initDB()

if __name__ == '__main__':
    socket.run(app, port=5500)