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

        type_membre = flask.request.form.get('type_membre', 'enfant').strip()
        success, reason = utils.createUser(username, password, lastname, firstname, email, age, gender, birthdate, type_membre)

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
    objets      = utils.searchObjets('', '', '')

    total    = len(objets)
    actifs   = sum(1 for o in objets if o['etat'] == 'actif')
    inactifs = total - actifs
    nb_types = len(set(o['type'] for o in objets))

    resp = flask.make_response(flask.render_template(
        'dashboard.html',
        user=flask.session.get('username'),
        user_data=user_data,
        connections=connections,
        objets=objets,
        stats={'total': total, 'actifs': actifs, 'inactifs': inactifs, 'types': nb_types}
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
    return flask.jsonify({'ok': True, 'points': float(user_data['points']), 'level': user_data['niveau']})

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

@app.route('/logout')
def logout():
    flask.session.clear()
    return flask.redirect('/')

@app.route('/search')
def search():
    query       = flask.request.args.get('q', '').strip()
    filtre_type = flask.request.args.get('type', '').strip()
    filtre_etat = flask.request.args.get('etat', '').strip()

    searched  = bool(query or filtre_type or filtre_etat)
    resultats = utils.searchObjets(query, filtre_type, filtre_etat) if searched else None
    types     = utils.getTypes()

    return flask.render_template(
        'search.html',
        user=flask.session.get('username'),
        resultats=resultats,
        types=types,
        query=query,
        filtre_type=filtre_type,
        filtre_etat=filtre_etat,
        searched=searched
    )

@app.route('/membres')
def membres():
    if 'username' not in flask.session:
        return flask.redirect('/login')
    all_members = utils.getAllMembers()
    return flask.render_template('membres.html', user=flask.session.get('username'), membres=all_members)

@app.route('/profil/<username>')
def profil_public(username):
    if 'username' not in flask.session:
        return flask.redirect('/login')
    membre = utils.getUser(username)
    if not membre:
        flask.abort(404)
    viewer = flask.session.get('username')
    is_owner = (viewer == username)
    is_admin = utils.getUser(viewer)['role'] == 'admin' if viewer else False
    return flask.render_template(
        'public_profile.html',
        user=viewer,
        membre=membre,
        is_owner=is_owner,
        is_admin=is_admin
    )

@app.route('/objet/<int:objet_id>')
def objet_detail(objet_id):
    objet = utils.getObjet(objet_id)
    if not objet:
        flask.abort(404)
    return flask.render_template('objet.html', user=flask.session.get('username'), objet=objet)

@app.route('/api/consult/<int:objet_id>', methods=['POST'])
def api_consult(objet_id):
    if 'username' not in flask.session:
        return flask.jsonify({'ok': False})
    objet = utils.getObjet(objet_id)
    if not objet:
        return flask.jsonify({'ok': False})
    utils.addPoints(flask.session['username'], 0.50)
    user_data  = utils.getUser(flask.session['username'])
    new_points = float(user_data['points'])
    socket.emit('points_update', {
        'points': new_points,
        'level': user_data['niveau']
    }, room=flask.session['username'])
    return flask.jsonify({'ok': True, 'points': new_points, 'level': user_data['niveau']})

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
    utils.createAdmin('admin', 'admin1234')

if __name__ == '__main__':
    socket.run(app, port=5500)