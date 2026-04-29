import os
import flask
import utils
import flask_socketio
import flask_mail
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join('static', 'uploads', 'photos')
ALLOWED_PHOTO_EXT = {'jpg', 'jpeg', 'png', 'gif', 'webp'}

app = flask.Flask(__name__, static_url_path='/static')
app.teardown_appcontext(utils.closeDB)
app.secret_key = "secret1234"

app.config['MAIL_SERVER']   = 'smtp.gmail.com'
app.config['MAIL_PORT']     = 587
app.config['MAIL_USE_TLS']  = True
app.config['MAIL_USERNAME'] = 'kentaroloret1@gmail.com'
app.config['MAIL_PASSWORD'] = 'ybwr tsfl dkgv bkcr'
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

mail = flask_mail.Mail(app)
socket = flask_socketio.SocketIO(app, async_mode='gevent')

_LEVEL_LABELS = {
    'debutant':      'Débutant',
    'intermediaire': 'Intermédiaire',
    'avance':        'Avancé',
    'expert':        'Expert',
}

@app.template_filter('level_label')
def level_label_filter(key: str) -> str:
    return _LEVEL_LABELS.get(key, key.capitalize())

def send_verification_email(to_email: str, username: str, token: str) -> bool:
    verify_url = flask.url_for('verify_email', token=token, _external=True)
    msg = flask_mail.Message('Validez votre inscription - OsmHome',
                             recipients=[to_email],
                             sender=app.config['MAIL_USERNAME'])
    msg.html = f'''
    <div style="font-family:sans-serif;max-width:480px;margin:auto">
      <h2 style="color:#1a73e8">Bienvenue sur OsmHome, {username} !</h2>
      <p>Cliquez sur le bouton ci-dessous pour valider votre adresse email et activer votre compte.</p>
      <a href="{verify_url}"
         style="display:inline-block;background:#1a73e8;color:#fff;padding:12px 24px;
                border-radius:8px;text-decoration:none;font-weight:600;margin:16px 0">
        Valider mon compte
      </a>
      <p style="color:#666;font-size:0.85rem">Ce lien est valable 24h. Si vous n\'avez pas créé de compte, ignorez cet email.</p>
    </div>
    '''
    try:
        mail.send(msg)
        return True
    except Exception as e:
        app.logger.error(f'[MAIL ERROR] {e}')
        return False

@app.route('/admin/test-mail')
def test_mail():
    username = flask.session.get('username')
    if not username or utils.getUser(username)['role'] != 'admin':
        flask.abort(403)
    cfg_user = app.config.get('MAIL_USERNAME', '')
    if not cfg_user:
        return 'MAIL_USERNAME non configuré', 400
    try:
        msg = flask_mail.Message('Test OsmHome', recipients=[cfg_user], sender=cfg_user)
        msg.body = 'Si vous recevez cet email, la configuration SMTP fonctionne.'
        mail.send(msg)
        return 'Email de test envoyé à ' + cfg_user
    except Exception as e:
        return f'Erreur : {e}', 500

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

        SIGNUP_ERRORS = {
            'username_taken': 'Ce pseudo est déjà utilisé, choisissez-en un autre.',
        }

        errors = []
        if not username:
            errors.append('Le pseudo est obligatoire.')
        if not password or len(password) < 6:
            errors.append('Le mot de passe doit contenir au moins 6 caractères.')
        if not lastname:
            errors.append('Le nom est obligatoire.')
        if not firstname:
            errors.append('Le prénom est obligatoire.')
        if not email or '@' not in email:
            errors.append('L\'adresse email est invalide.')
        if not age or not age.isdigit() or not (1 <= int(age) <= 120):
            errors.append('L\'âge doit être un nombre valide.')
        if not birthdate:
            errors.append('La date de naissance est obligatoire.')

        if errors:
            return flask.render_template('signup.html', user=None,
                error=' '.join(errors), form=flask.request.form)

        success, reason = utils.createUser(username, password, lastname, firstname, email, age, gender, birthdate, member_type)

        if success:
            token = reason
            reg_mode = utils.getSetting('registration_mode', 'email')
            if reg_mode == 'libre':
                utils.verifyEmail(token)
                flask.session['username'] = username
                utils.recordConnection(username)
                return flask.redirect('/dashboard')
            elif reg_mode == 'approval':
                flask.session['pending_verification'] = username
                return flask.redirect('/verify-pending')
            else:
                smtp_configured = bool(app.config.get('MAIL_USERNAME'))
                if smtp_configured:
                    send_verification_email(email, username, token)
                else:
                    utils.verifyEmail(token)
                    flask.session['username'] = username
                    utils.recordConnection(username)
                    return flask.redirect('/dashboard')
                flask.session['pending_verification'] = username
                return flask.redirect('/verify-pending')
        else:
            return flask.render_template('signup.html', user=None,
                error=SIGNUP_ERRORS.get(reason, 'Erreur lors de la création du compte.'),
                form=flask.request.form)
    else:
        return flask.render_template('signup.html', user=flask.session.get('username'))

LOGIN_ERRORS = {
    'empty':          'Veuillez remplir tous les champs.',
    'user_not_found': 'Aucun compte trouvé avec ce pseudo.',
    'wrong_password': 'Mot de passe incorrect.',
}

@app.route('/login', methods=['GET','POST'])
def login():
    if flask.request.method == 'POST':
        username = flask.request.form.get('username', '').strip()
        password = flask.request.form.get('password', '').strip()

        if not username or not password:
            return flask.render_template('login.html', user=None, error=LOGIN_ERRORS['empty'], form_username=username)

        success, reason = utils.loginUser(username, password)

        if success:
            user_data = utils.getUser(username)
            if not user_data['email_verified']:
                flask.session['pending_verification'] = username
                return flask.redirect('/verify-pending')
            flask.session['username'] = username
            utils.recordConnection(username)
            return flask.redirect('/dashboard')
        else:
            return flask.render_template('login.html', user=None, error=LOGIN_ERRORS.get(reason, 'Erreur de connexion.'), form_username=username)
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
        return flask.jsonify({'ok': True, 'level': result, 'points': float(user_data['points'])})
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

@app.route('/verify-pending')
def verify_pending():
    username = flask.session.get('pending_verification')
    if not username:
        return flask.redirect('/login')
    user_data = utils.getUser(username)
    if not user_data:
        return flask.redirect('/login')
    if user_data['email_verified']:
        flask.session.pop('pending_verification', None)
        flask.session['username'] = username
        return flask.redirect('/dashboard')
    email = user_data['email'] or ''
    masked = email[:2] + '***' + email[email.find('@'):] if '@' in email else email
    return flask.render_template('verify_pending.html', user=None, email_masked=masked)

@app.route('/verify/<token>')
def verify_email(token):
    success, result = utils.verifyEmail(token)
    if not success:
        return flask.render_template('verify_pending.html', user=None,
            email_masked='', error='Lien invalide ou expiré.')
    flask.session.pop('pending_verification', None)
    flask.session['username'] = result
    utils.recordConnection(result)
    return flask.redirect('/dashboard')

@app.route('/resend-verification', methods=['POST'])
def resend_verification():
    username = flask.session.get('pending_verification')
    if not username:
        return flask.redirect('/login')
    user_data = utils.getUser(username)
    if not user_data or user_data['email_verified']:
        return flask.redirect('/dashboard')
    token = utils.regenerateToken(username)
    send_verification_email(user_data['email'], username, token)
    return flask.render_template('verify_pending.html', user=None,
        email_masked='', resent=True)

@app.route('/profile/change-password', methods=['POST'])
def profile_change_password():
    if 'username' not in flask.session:
        return flask.jsonify({'ok': False, 'error': 'not_logged_in'}), 401
    data = flask.request.get_json()
    current = data.get('current_password', '')
    new_pw  = data.get('new_password', '')
    confirm = data.get('confirm_password', '')
    if new_pw != confirm:
        return flask.jsonify({'ok': False, 'error': 'mismatch'})
    success, reason = utils.changePassword(flask.session['username'], current, new_pw)
    if success:
        return flask.jsonify({'ok': True})
    return flask.jsonify({'ok': False, 'error': reason})

@app.route('/profile/photo', methods=['POST'])
def profile_photo():
    if 'username' not in flask.session:
        return flask.jsonify({'ok': False}), 401
    file = flask.request.files.get('photo')
    if not file or file.filename == '':
        return flask.jsonify({'ok': False, 'error': 'no_file'})
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_PHOTO_EXT:
        return flask.jsonify({'ok': False, 'error': 'invalid_type'})
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filename = secure_filename(flask.session['username']) + '.' + ext
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    utils.updatePhoto(flask.session['username'], filename)
    return flask.jsonify({'ok': True, 'filename': filename})

@app.route('/logout')
def logout():
    flask.session.clear()
    return flask.redirect('/')

@app.route('/search')
def search():
    query         = flask.request.args.get('q', '').strip()
    filter_type   = flask.request.args.get('type', '').strip()
    filter_status = flask.request.args.get('status', '').strip()
    filter_room   = flask.request.args.get('room', '').strip()

    searched = bool(query or filter_type or filter_status or filter_room)
    results  = utils.searchDevices(query, filter_type, filter_status, filter_room) if searched else None
    types    = utils.getTypes()
    rooms    = utils.getRooms()

    return flask.render_template(
        'search.html',
        user=flask.session.get('username'),
        results=results,
        types=types,
        rooms=rooms,
        query=query,
        filter_type=filter_type,
        filter_status=filter_status,
        filter_room=filter_room,
        searched=searched
    )

@app.route('/services')
def services():
    all_services = utils.getAllServices()
    return flask.render_template('services.html', user=flask.session.get('username'), all_services=all_services)

@app.route('/service/<slug>')
def service_detail(slug):
    if 'username' not in flask.session:
        return flask.redirect('/login')
    service = utils.getServiceBySlug(slug)
    if not service:
        flask.abort(404)
    viewer_data = utils.getUser(flask.session['username'])
    if service['access'] == 'restreint' and viewer_data['level'] not in ('avance', 'expert') and viewer_data['role'] != 'admin':
        flask.abort(403)

    if slug == 'planning':
        utils.executeDuePlannings()

    extra_data = utils.getServiceExtraData(slug)
    plannings = utils.getPlannings(flask.session['username']) if slug == 'planning' else []
    all_devices = utils.searchDevices('', '', '') if slug == 'planning' else []

    utils.addPoints(flask.session['username'], 0.50)
    utils.incrementActions(flask.session['username'])
    user_data = utils.getUser(flask.session['username'])
    socket.emit('points_update', {
        'points': float(user_data['points']),
        'level': user_data['level']
    }, room=flask.session['username'])

    return flask.render_template(
        'service.html',
        user=flask.session.get('username'),
        service=service,
        data=extra_data,
        plannings=plannings,
        all_devices=all_devices,
        viewer_data=viewer_data,
    )

@app.route('/api/service/group-toggle', methods=['POST'])
def api_group_toggle():
    if 'username' not in flask.session:
        return flask.jsonify({'ok': False}), 401
    u = utils.getUser(flask.session['username'])
    if not u or (u['level'] not in ('avance', 'expert') and u['role'] != 'admin'):
        return flask.jsonify({'ok': False}), 403
    data = flask.request.get_json(silent=True) or {}
    type_ = data.get('type', '').strip()
    action = data.get('action', '').strip()
    if not type_ or action not in ('activer', 'désactiver'):
        return flask.jsonify({'ok': False, 'error': 'invalid_params'})
    count = utils.toggleDevicesByType(type_, action)
    utils.addPoints(flask.session['username'], 0.10)
    user_data = utils.getUser(flask.session['username'])
    socket.emit('points_update', {
        'points': float(user_data['points']),
        'level': user_data['level']
    }, room=flask.session['username'])
    return flask.jsonify({'ok': True, 'count': count, 'action': action, 'new_status': 'actif' if action == 'activer' else 'inactif'})

@app.route('/api/service/planning', methods=['POST'])
def api_add_planning():
    if 'username' not in flask.session:
        return flask.jsonify({'ok': False}), 401
    u = utils.getUser(flask.session['username'])
    if not u or (u['level'] not in ('avance', 'expert') and u['role'] != 'admin'):
        return flask.jsonify({'ok': False}), 403
    data = flask.request.get_json(silent=True) or {}
    device_id = data.get('device_id')
    action = data.get('action', '')
    scheduled_at = data.get('scheduled_at', '')
    if not device_id or not action or not scheduled_at:
        return flask.jsonify({'ok': False, 'error': 'missing_fields'})
    success, reason = utils.addPlanning(flask.session['username'], device_id, action, scheduled_at)
    return flask.jsonify({'ok': success, 'reason': reason})

@app.route('/api/service/planning/<int:pid>/delete', methods=['POST'])
def api_delete_planning(pid):
    if 'username' not in flask.session:
        return flask.jsonify({'ok': False}), 401
    utils.deletePlanning(pid, flask.session['username'])
    return flask.jsonify({'ok': True})

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
    utils.incrementActions(flask.session['username'])
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

def _is_admin() -> bool:
    if 'username' not in flask.session:
        return False
    u = utils.getUser(flask.session['username'])
    return bool(u and u['role'] == 'admin')

@app.route('/admin')
def admin():
    if not _is_admin():
        flask.abort(403)
    stats        = utils.getAdminStats()
    pending_users = utils.getPendingUsers()
    reg_mode     = utils.getSetting('registration_mode', 'email')
    full_stats   = utils.getAdminFullStats()
    active_tab   = flask.request.args.get('tab', 'utilisateurs')
    saved        = flask.request.args.get('saved') == '1'
    return flask.render_template('admin.html',
        user=flask.session.get('username'),
        stats=stats,
        pending_users=pending_users,
        reg_mode=reg_mode,
        full_stats=full_stats,
        active_tab=active_tab,
        saved=saved,
    )

@app.context_processor
def inject_types():
    try:
        types = utils.getTypes()
    except Exception:
        types = []
    is_admin = False
    user_level = None
    if flask.session.get('username'):
        u = utils.getUser(flask.session['username'])
        is_admin = bool(u and u['role'] == 'admin')
        user_level = u['level'] if u else None
    return {'types': types, 'is_admin': is_admin, 'user_level': user_level}

def _require_gestion():
    if 'username' not in flask.session:
        return flask.redirect('/login')
    u = utils.getUser(flask.session['username'])
    if not u or u['level'] not in ('avance', 'expert'):
        flask.abort(403)
    return None

def _require_expert():
    if 'username' not in flask.session:
        return flask.redirect('/login')
    u = utils.getUser(flask.session['username'])
    if not u or u['level'] != 'expert':
        flask.abort(403)
    return None

@app.route('/gestion')
def gestion():
    r = _require_gestion()
    if r: return r
    devices = utils.getDevicesForGestion()
    stats   = utils.getGestionStats()
    return flask.render_template('gestion.html', user=flask.session.get('username'),
                                 devices=devices, stats=stats)

@app.route('/gestion/device/add', methods=['GET', 'POST'])
def gestion_device_add():
    r = _require_expert()
    if r: return r
    if flask.request.method == 'POST':
        f = flask.request.form
        battery = f.get('battery', '').strip()
        battery = int(battery) if battery.isdigit() else None
        success, result = utils.addDevice(
            f.get('name','').strip(), f.get('description','').strip(),
            f.get('type','').strip(), f.get('brand','').strip(),
            f.get('status','actif'), f.get('connectivity','').strip(),
            battery, f.get('room','').strip(), f.get('config','').strip() or None
        )
        if success:
            return flask.redirect('/gestion')
        return flask.render_template('gestion_form.html', user=flask.session.get('username'),
                                     device=None, error='Erreur lors de l\'ajout.')
    return flask.render_template('gestion_form.html', user=flask.session.get('username'), device=None)

@app.route('/gestion/device/<int:device_id>/edit', methods=['GET', 'POST'])
def gestion_device_edit(device_id):
    r = _require_expert()
    if r: return r
    device = utils.getDevice(device_id)
    if not device:
        flask.abort(404)
    if flask.request.method == 'POST':
        f = flask.request.form
        battery = f.get('battery', '').strip()
        battery = int(battery) if battery.isdigit() else None
        success, _ = utils.updateDevice(
            device_id, f.get('name','').strip(), f.get('description','').strip(),
            f.get('type','').strip(), f.get('brand','').strip(),
            f.get('status','actif'), f.get('connectivity','').strip(),
            battery, f.get('room','').strip(), f.get('config','').strip() or None
        )
        if success:
            return flask.redirect('/gestion')
        return flask.render_template('gestion_form.html', user=flask.session.get('username'),
                                     device=device, error='Erreur lors de la modification.')
    return flask.render_template('gestion_form.html', user=flask.session.get('username'), device=device)

@app.route('/api/gestion/device/<int:device_id>/toggle', methods=['POST'])
def gestion_device_toggle(device_id):
    r = _require_gestion()
    if r: return flask.jsonify({'ok': False}), 403
    success, result = utils.toggleDeviceStatus(device_id)
    return flask.jsonify({'ok': success, 'status': result if success else None})

@app.route('/api/gestion/device/<int:device_id>/request-delete', methods=['POST'])
def gestion_request_delete(device_id):
    r = _require_gestion()
    if r: return flask.jsonify({'ok': False}), 403
    device = utils.getDevice(device_id)
    if not device:
        return flask.jsonify({'ok': False})
    if device['deletion_requested']:
        utils.cancelDeviceDeletion(device_id)
        return flask.jsonify({'ok': True, 'requested': False})
    utils.requestDeviceDeletion(device_id)
    return flask.jsonify({'ok': True, 'requested': True})

@app.route('/admin/device/<int:device_id>/delete', methods=['POST'])
def admin_device_delete(device_id):
    if 'username' not in flask.session:
        return flask.redirect('/login')
    u = utils.getUser(flask.session['username'])
    if not u or u['role'] != 'admin':
        flask.abort(403)
    utils.adminDeleteDevice(device_id)
    return flask.redirect('/gestion')

@app.route('/admin/user/<username>/reset-password', methods=['POST'])
def admin_reset_password(username):
    if not _is_admin():
        return flask.jsonify({'ok': False}), 403
    data = flask.request.get_json(silent=True) or {}
    new_pw = data.get('password', '').strip()
    success, reason = utils.adminResetPassword(username, new_pw)
    return flask.jsonify({'ok': success, 'reason': reason})

@app.route('/admin/backup')
def admin_backup():
    if not _is_admin():
        flask.abort(403)
    import os
    return flask.send_file(os.path.abspath(utils.BASE), as_attachment=True,
                           download_name='osmhome_backup.db',
                           mimetype='application/octet-stream')

@app.route('/admin/integrity')
def admin_integrity():
    if not _is_admin():
        flask.abort(403)
    return flask.jsonify(utils.checkIntegrity())

@app.route('/admin/export/users')
def admin_export_users():
    if not _is_admin():
        flask.abort(403)
    import csv, io
    rows = utils.getAdminStats()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(['username', 'member_type', 'level', 'points', 'connections', 'actions'])
    for r in rows:
        w.writerow([r['username'], r['member_type'], r['level'], r['points'],
                    r['connection_count'], r['actions'] or 0])
    out.seek(0)
    return flask.Response(out.getvalue(), mimetype='text/plain',
        headers={'Content-Disposition': 'attachment; filename=users.txt'})

@app.route('/admin/export/devices')
def admin_export_devices():
    if not _is_admin():
        flask.abort(403)
    import csv, io
    devices = utils.getDevicesForGestion()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(['id', 'name', 'type', 'brand', 'room', 'connectivity', 'battery', 'status'])
    for d in devices:
        w.writerow([d['id'], d['name'], d['type'], d['brand'] or '',
                    d['room'] or '', d['connectivity'] or '', d['battery'] or '', d['status']])
    out.seek(0)
    return flask.Response(out.getvalue(), mimetype='text/plain',
        headers={'Content-Disposition': 'attachment; filename=devices.txt'})

@app.route('/admin/settings', methods=['POST'])
def admin_save_settings():
    if not _is_admin():
        flask.abort(403)
    reg_mode = flask.request.form.get('registration_mode', 'email')
    if reg_mode not in ('libre', 'email', 'approval'):
        reg_mode = 'email'
    utils.setSetting('registration_mode', reg_mode)
    return flask.redirect('/admin?tab=personnalisation&saved=1')

@app.route('/admin/user/<username>/approve', methods=['POST'])
def admin_approve_user(username):
    if not _is_admin():
        flask.abort(403)
    utils.approveUser(username)
    return flask.redirect('/admin?tab=personnalisation')

@app.route('/admin/user/<username>/deny', methods=['POST'])
def admin_deny_user(username):
    if not _is_admin():
        flask.abort(403)
    utils.denyUser(username)
    return flask.redirect('/admin?tab=personnalisation')

@app.route('/gestion/reports')
def gestion_reports():
    r = _require_expert()
    if r: return r
    stats = utils.getGestionStats()
    return flask.render_template('gestion_reports.html', user=flask.session.get('username'), stats=stats)

with app.app_context():
    utils.initDB()
    utils.seedServices()
    existing = utils.getUser('testuser')
    if existing:
        utils.deleteUser('testuser')
    _, token = utils.createUser('testuser', 'test123', 'Test', 'User',
                                'testuser@osmhome.fr', '20', 'male', '2004-01-01', 'fils')
    utils.verifyEmail(token)

if __name__ == '__main__':
    socket.run(app, port=5500)