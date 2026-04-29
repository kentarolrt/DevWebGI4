import sqlite3
import secrets
import datetime
import flask
from werkzeug.security import generate_password_hash, check_password_hash

BASE = 'base.db'

def openDB() -> sqlite3.Connection:
    if 'db' not in flask.g:
        flask.g.db = sqlite3.connect(BASE)
        flask.g.db.row_factory = sqlite3.Row
    return flask.g.db


def closeDB(_ = None):
    db = flask.g.pop("db", None)
    if db is not None:
        db.close()

def initDB():
    db = openDB()
    db.executescript(''' 
        PRAGMA journal_mode = WAL;
        PRAGMA synchronous = NORMAL;
        PRAGMA foreign_keys = ON;
        PRAGMA temp_store = MEMORY;
        PRAGMA busy_timeout = 5000;
                     
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            lastname TEXT,
            firstname TEXT,
            age INTEGER,
            gender TEXT,
            birthdate TEXT,
            member_type TEXT,
            photo TEXT,
            level TEXT DEFAULT 'debutant',
            points REAL DEFAULT 0,
            email TEXT,
            email_verified INTEGER DEFAULT 0,
            role TEXT DEFAULT 'simple'
        );

        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            type TEXT,
            brand TEXT,
            status TEXT DEFAULT 'actif',
            connectivity TEXT,
            battery INTEGER,
            room TEXT
        );

        CREATE TABLE IF NOT EXISTS connection_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            connected_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            category TEXT,
            access TEXT DEFAULT 'libre'
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        INSERT OR IGNORE INTO settings (key, value) VALUES ('registration_mode', 'email');
    ''')

    db.commit()

    try:
        db.execute('ALTER TABLE users ADD COLUMN actions INTEGER DEFAULT 0')
        db.commit()
    except Exception:
        pass

    try:
        db.execute('ALTER TABLE users ADD COLUMN verification_token TEXT')
        db.commit()
    except Exception:
        pass

    try:
        db.execute('ALTER TABLE devices ADD COLUMN deletion_requested INTEGER DEFAULT 0')
        db.commit()
    except Exception:
        pass

    try:
        db.execute('ALTER TABLE devices ADD COLUMN config TEXT')
        db.commit()
    except Exception:
        pass

    try:
        db.execute('ALTER TABLE services ADD COLUMN slug TEXT')
        db.commit()
    except Exception:
        pass

    db.executescript('''
        CREATE TABLE IF NOT EXISTS plannings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            device_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            scheduled_at TEXT NOT NULL,
            executed INTEGER DEFAULT 0
        );
    ''')
    db.commit()


MEMBER_TYPES = ['père', 'mère', 'fils', 'fille']

def createUser(username, password, lastname, firstname, email, age, gender, birthdate, member_type='fils') -> tuple[bool, str]:
    db = openDB()

    existing = db.execute(
        'SELECT id FROM users WHERE username = ?',
        (username,)
    ).fetchone()

    if existing:
        return False, 'username_taken'

    if member_type not in MEMBER_TYPES:
        member_type = 'fils'

    role = 'admin' if member_type in ('père', 'mère') else 'simple'
    level = 'expert' if member_type in ('père', 'mère') else 'debutant'
    token = secrets.token_urlsafe(32)

    db.execute(
        'INSERT INTO users (username, password, lastname, firstname, email, age, gender, birthdate, member_type, role, level, verification_token) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (username, generate_password_hash(password), lastname, firstname, email, age, gender, birthdate, member_type, role, level, token)
    )

    db.commit()

    return True, token


def verifyEmail(token: str) -> tuple[bool, str]:
    db = openDB()
    user = db.execute('SELECT id, username FROM users WHERE verification_token = ?', (token,)).fetchone()
    if not user:
        return False, 'invalid_token'
    db.execute('UPDATE users SET email_verified = 1, verification_token = NULL WHERE id = ?', (user['id'],))
    db.commit()
    return True, user['username']

def regenerateToken(username: str) -> str:
    db = openDB()
    token = secrets.token_urlsafe(32)
    db.execute('UPDATE users SET verification_token = ? WHERE username = ?', (token, username))
    db.commit()
    return token

def loginUser(username, password) -> tuple[bool, str]:
    db = openDB()

    user = db.execute(
        'SELECT * FROM users WHERE username = ?',
        (username,)
    ).fetchone()

    if not user:
        return False, 'user_not_found'
    
    if not check_password_hash(user['password'], password):
        return False, 'wrong_password'
    
    return True, 'ok'

def getUser(username: str):
    db = openDB()
    return db.execute(
        'SELECT * FROM users WHERE username = ?',
        (username,)
    ).fetchone()

ALLOWED_FIELDS = {'username', 'email', 'lastname', 'firstname', 'age', 'gender', 'birthdate', 'member_type'}

def updateUser(username: str, field: str, value: str) -> tuple[bool, str]:
    if field not in ALLOWED_FIELDS:
        return False, 'field_not_allowed'

    db = openDB()

    if field == 'username':
        existing = db.execute(
            'SELECT id FROM users WHERE username = ?', (value,)
        ).fetchone()
        if existing:
            return False, 'username_taken'

    db.execute(
        f'UPDATE users SET {field} = ? WHERE username = ?',
        (value, username)
    )
    db.commit()
    return True, 'ok'

def searchDevices(query='', filter_type='', filter_status='', filter_room='') -> list:
    db = openDB()

    sql = 'SELECT * FROM devices WHERE 1=1'
    params = []

    if query:
        sql += ' AND (name LIKE ? OR description LIKE ?)'
        params.extend([f'%{query}%', f'%{query}%'])

    if filter_type:
        sql += ' AND type = ?'
        params.append(filter_type)

    if filter_status:
        sql += ' AND status = ?'
        params.append(filter_status)

    if filter_room:
        sql += ' AND room = ?'
        params.append(filter_room)

    sql += ' ORDER BY name'
    return db.execute(sql, params).fetchall()

def getRooms() -> list:
    db = openDB()
    rows = db.execute(
        'SELECT DISTINCT room FROM devices WHERE room IS NOT NULL AND room != "" ORDER BY room'
    ).fetchall()
    return [row['room'] for row in rows]

def getConnectionCount(username: str) -> int:
    db = openDB()
    user = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    if not user:
        return 0
    row = db.execute(
        'SELECT COUNT(*) as cnt FROM connection_history WHERE user_id = ?',
        (user['id'],)
    ).fetchone()
    return row['cnt'] if row else 0

def getTypes() -> list:
    db = openDB()
    rows = db.execute('SELECT DISTINCT type FROM devices ORDER BY type').fetchall()
    return [row['type'] for row in rows]

def addPoints(username: str, amount: float) -> None:
    db = openDB()
    db.execute('UPDATE users SET points = points + ? WHERE username = ?', (amount, username))
    db.commit()

_LEVEL_THRESHOLDS = {'debutant': 0, 'intermediaire': 1, 'avance': 3, 'expert': 5}

def upgradeLevel(username: str) -> tuple[bool, str]:
    db = openDB()
    user = db.execute('SELECT points, level FROM users WHERE username = ?', (username,)).fetchone()
    if not user:
        return False, 'user_not_found'
    levels = ['debutant', 'intermediaire', 'avance', 'expert']
    current_idx = levels.index(user['level'])
    if current_idx >= len(levels) - 1:
        return False, 'already_max'
    next_level = levels[current_idx + 1]
    if user['points'] < _LEVEL_THRESHOLDS[next_level]:
        return False, 'not_enough_points'
    if next_level == 'expert':
        db.execute('UPDATE users SET level = ?, role = ? WHERE username = ?', (next_level, 'admin', username))
    else:
        db.execute('UPDATE users SET level = ? WHERE username = ?', (next_level, username))
    db.commit()
    return True, next_level

def incrementActions(username: str) -> None:
    db = openDB()
    db.execute('UPDATE users SET actions = actions + 1 WHERE username = ?', (username,))
    db.commit()

def recordConnection(username: str) -> None:
    db = openDB()
    user = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    if user:
        db.execute('INSERT INTO connection_history (user_id) VALUES (?)', (user['id'],))
        db.commit()
    incrementActions(username)
    addPoints(username, 0.25)

def getAdminStats() -> list:
    db = openDB()
    return db.execute('''
        SELECT u.username, u.member_type, u.level, u.points, u.actions,
               COUNT(c.id) AS connection_count
        FROM users u
        LEFT JOIN connection_history c ON c.user_id = u.id
        GROUP BY u.id
        ORDER BY connection_count DESC
    ''').fetchall()

def getDevice(device_id: int):
    db = openDB()
    return db.execute('SELECT * FROM devices WHERE id = ?', (device_id,)).fetchone()

def searchServices(query='', filter_category='', filter_access='') -> list:
    db = openDB()
    sql = 'SELECT * FROM services WHERE 1=1'
    params = []
    if query:
        sql += ' AND (name LIKE ? OR description LIKE ?)'
        params.extend([f'%{query}%', f'%{query}%'])
    if filter_category:
        sql += ' AND category = ?'
        params.append(filter_category)
    if filter_access:
        sql += ' AND access = ?'
        params.append(filter_access)
    sql += ' ORDER BY category, name'
    return db.execute(sql, params).fetchall()

def getService(service_id: int):
    db = openDB()
    return db.execute('SELECT * FROM services WHERE id = ?', (service_id,)).fetchone()

def getCategories() -> list:
    db = openDB()
    rows = db.execute('SELECT DISTINCT category FROM services ORDER BY category').fetchall()
    return [row['category'] for row in rows]

def getServiceBySlug(slug: str):
    db = openDB()
    return db.execute('SELECT * FROM services WHERE slug = ?', (slug,)).fetchone()

def getAllServices() -> list:
    db = openDB()
    return db.execute('SELECT * FROM services ORDER BY id').fetchall()

def seedServices():
    db = openDB()
    existing = db.execute('SELECT COUNT(*) as cnt FROM services WHERE slug IS NOT NULL').fetchone()['cnt']
    if existing >= 5:
        return
    db.execute('DELETE FROM services')
    try:
        db.execute("DELETE FROM sqlite_sequence WHERE name='services'")
    except Exception:
        pass
    rows = [
        ('Rapport énergétique',
         'Consultez en temps réel les statistiques de consommation et l\'état de vos appareils.',
         'Énergie', 'libre', 'rapport-energie'),
        ('Contrôle de groupe',
         'Activez ou désactivez tous les appareils d\'un même type en un seul clic.',
         'Automatisation', 'restreint', 'controle-groupe'),
        ('Surveillance sécurité',
         'Surveillez l\'état de vos caméras, serrures et capteurs, et recevez des alertes.',
         'Sécurité', 'libre', 'surveillance'),
        ('Planning',
         'Programmez des actions automatiques sur vos appareils à l\'heure de votre choix.',
         'Automatisation', 'restreint', 'planning'),
        ('Diagnostic système',
         'Analysez la santé de vos appareils : batterie, connectivité et état général.',
         'Santé', 'libre', 'diagnostic'),
    ]
    db.executemany(
        'INSERT INTO services (name, description, category, access, slug) VALUES (?,?,?,?,?)', rows
    )
    db.commit()

def getServiceExtraData(slug: str) -> dict:
    db = openDB()
    if slug == 'rapport-energie':
        devices = db.execute('SELECT * FROM devices').fetchall()
        total = len(devices)
        active = sum(1 for d in devices if d['status'] == 'actif')
        battery_devs = [d for d in devices if d['battery'] is not None]
        avg_battery = round(sum(d['battery'] for d in battery_devs) / len(battery_devs)) if battery_devs else None
        low_battery = [d for d in battery_devs if d['battery'] < 20]
        by_type = {}
        for d in devices:
            t = d['type']
            if t not in by_type:
                by_type[t] = {'total': 0, 'active': 0}
            by_type[t]['total'] += 1
            if d['status'] == 'actif':
                by_type[t]['active'] += 1
        return {
            'total': total, 'active': active, 'inactive': total - active,
            'avg_battery': avg_battery, 'low_battery': low_battery, 'by_type': by_type,
        }

    if slug == 'controle-groupe':
        devices = db.execute('SELECT * FROM devices ORDER BY type, name').fetchall()
        by_type = {}
        for d in devices:
            t = d['type']
            if t not in by_type:
                by_type[t] = {'devices': [], 'active': 0, 'total': 0}
            by_type[t]['devices'].append(dict(d))
            by_type[t]['total'] += 1
            if d['status'] == 'actif':
                by_type[t]['active'] += 1
        return {'by_type': by_type}

    if slug == 'surveillance':
        security_types = ('caméra', 'serrure', 'capteur')
        devices = db.execute(
            'SELECT * FROM devices WHERE type IN (?,?,?) ORDER BY type, name', security_types
        ).fetchall()
        alerts = [d for d in devices if d['status'] == 'inactif']
        return {'devices': devices, 'alerts': alerts}

    if slug == 'diagnostic':
        devices = db.execute('SELECT * FROM devices ORDER BY name').fetchall()
        issues = []
        for d in devices:
            issue_list = []
            if d['battery'] is not None and d['battery'] < 20:
                issue_list.append(f'Batterie faible ({d["battery"]}%)')
            if d['status'] == 'inactif':
                issue_list.append('Inactif')
            if issue_list:
                issues.append({'device': dict(d), 'issues': issue_list})
        issue_ids = {item['device']['id'] for item in issues}
        return {
            'devices': devices,
            'issues': issues,
            'issue_ids': issue_ids,
            'total': len(devices),
            'healthy': len(devices) - len(issues),
        }

    return {}

def drainBatteries() -> None:
    db = openDB()
    db.execute(
        "UPDATE devices SET battery = battery - 1 WHERE battery > 0 AND status = 'actif' AND battery IS NOT NULL"
    )
    db.execute(
        "UPDATE devices SET status = 'inactif' WHERE battery IS NOT NULL AND battery <= 0 AND status = 'actif'"
    )
    db.commit()

def toggleDevicesByType(type_: str, action: str) -> int:
    db = openDB()
    new_status = 'actif' if action == 'activer' else 'inactif'
    cursor = db.execute('UPDATE devices SET status = ? WHERE type = ?', (new_status, type_))
    db.commit()
    return cursor.rowcount

def getPlannings(username: str) -> list:
    db = openDB()
    return db.execute(
        '''SELECT p.*, d.name as device_name
           FROM plannings p JOIN devices d ON d.id = p.device_id
           WHERE p.username = ? AND p.executed = 0
           ORDER BY p.scheduled_at''',
        (username,)
    ).fetchall()

def addPlanning(username: str, device_id: int, action: str, scheduled_at: str) -> tuple:
    db = openDB()
    if not db.execute('SELECT id FROM devices WHERE id = ?', (device_id,)).fetchone():
        return False, 'device_not_found'
    if action not in ('activer', 'désactiver'):
        return False, 'invalid_action'
    db.execute(
        'INSERT INTO plannings (username, device_id, action, scheduled_at) VALUES (?,?,?,?)',
        (username, device_id, action, scheduled_at)
    )
    db.commit()
    return True, 'ok'

def deletePlanning(planning_id: int, username: str) -> bool:
    db = openDB()
    db.execute('DELETE FROM plannings WHERE id = ? AND username = ?', (planning_id, username))
    db.commit()
    return True

def executeDuePlannings() -> int:
    now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M')
    db = openDB()
    due = db.execute(
        'SELECT * FROM plannings WHERE executed = 0 AND scheduled_at <= ?', (now,)
    ).fetchall()
    count = 0
    for p in due:
        new_status = 'actif' if p['action'] == 'activer' else 'inactif'
        db.execute('UPDATE devices SET status = ? WHERE id = ?', (new_status, p['device_id']))
        db.execute('UPDATE plannings SET executed = 1 WHERE id = ?', (p['id'],))
        count += 1
    if count:
        db.commit()
    return count

def getAllMembers() -> list:
    db = openDB()
    return db.execute(
        'SELECT username, age, gender, birthdate, member_type, level, points FROM users ORDER BY member_type, username'
    ).fetchall()

def addDevice(name, description, type_, brand, status, connectivity, battery, room, config=None):
    db = openDB()
    cursor = db.execute(
        'INSERT INTO devices (name, description, type, brand, status, connectivity, battery, room, config) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (name, description, type_, brand, status, connectivity, battery or None, room or None, config)
    )
    db.commit()
    return True, cursor.lastrowid

def updateDevice(device_id, name, description, type_, brand, status, connectivity, battery, room, config=None):
    db = openDB()
    if not db.execute('SELECT id FROM devices WHERE id = ?', (device_id,)).fetchone():
        return False, 'not_found'
    db.execute(
        'UPDATE devices SET name=?, description=?, type=?, brand=?, status=?, connectivity=?, battery=?, room=?, config=? WHERE id=?',
        (name, description, type_, brand, status, connectivity, battery or None, room or None, config, device_id)
    )
    db.commit()
    return True, 'ok'

def toggleDeviceStatus(device_id):
    db = openDB()
    device = db.execute('SELECT id, status FROM devices WHERE id = ?', (device_id,)).fetchone()
    if not device:
        return False, 'not_found'
    new_status = 'inactif' if device['status'] == 'actif' else 'actif'
    db.execute('UPDATE devices SET status = ? WHERE id = ?', (new_status, device_id))
    db.commit()
    return True, new_status

def requestDeviceDeletion(device_id):
    db = openDB()
    db.execute('UPDATE devices SET deletion_requested = 1 WHERE id = ?', (device_id,))
    db.commit()

def cancelDeviceDeletion(device_id):
    db = openDB()
    db.execute('UPDATE devices SET deletion_requested = 0 WHERE id = ?', (device_id,))
    db.commit()

def adminDeleteDevice(device_id):
    db = openDB()
    db.execute('DELETE FROM devices WHERE id = ?', (device_id,))
    db.commit()

def getDevicesForGestion():
    db = openDB()
    return db.execute('SELECT * FROM devices ORDER BY type, name').fetchall()

def getGestionStats():
    db = openDB()
    devices = db.execute('SELECT * FROM devices').fetchall()
    total = len(devices)
    active = sum(1 for d in devices if d['status'] == 'actif')
    pending_delete = sum(1 for d in devices if d['deletion_requested'])
    low_battery = [d for d in devices if d['battery'] is not None and d['battery'] < 20]
    by_type = {}
    for d in devices:
        t = d['type']
        if t not in by_type:
            by_type[t] = {'total': 0, 'active': 0}
        by_type[t]['total'] += 1
        if d['status'] == 'actif':
            by_type[t]['active'] += 1
    return {
        'total': total, 'active': active, 'inactive': total - active,
        'pending_delete': pending_delete, 'low_battery': low_battery, 'by_type': by_type,
    }

def changePassword(username: str, current_password: str, new_password: str) -> tuple[bool, str]:
    db = openDB()
    user = db.execute('SELECT password FROM users WHERE username = ?', (username,)).fetchone()
    if not user:
        return False, 'user_not_found'
    if not check_password_hash(user['password'], current_password):
        return False, 'wrong_password'
    if len(new_password) < 6:
        return False, 'too_short'
    db.execute('UPDATE users SET password = ? WHERE username = ?', (generate_password_hash(new_password), username))
    db.commit()
    return True, 'ok'

def updatePhoto(username: str, filename: str) -> None:
    db = openDB()
    db.execute('UPDATE users SET photo = ? WHERE username = ?', (filename, username))
    db.commit()

def deleteUser(username: str) -> tuple[bool, str]:
    db = openDB()
    user = db.execute('SELECT id, role FROM users WHERE username = ?', (username,)).fetchone()
    if not user:
        return False, 'user_not_found'
    db.execute('DELETE FROM connection_history WHERE user_id = ?', (user['id'],))
    db.execute('DELETE FROM users WHERE username = ?', (username,))
    db.commit()
    return True, 'ok'

def getSetting(key: str, default: str = '') -> str:
    db = openDB()
    row = db.execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchone()
    return row['value'] if row else default

def setSetting(key: str, value: str) -> None:
    db = openDB()
    db.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
    db.commit()

def adminResetPassword(username: str, new_password: str) -> tuple[bool, str]:
    if len(new_password) < 6:
        return False, 'too_short'
    db = openDB()
    user = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    if not user:
        return False, 'not_found'
    db.execute('UPDATE users SET password = ? WHERE username = ?',
               (generate_password_hash(new_password), username))
    db.commit()
    return True, 'ok'

def checkIntegrity() -> dict:
    db = openDB()
    integrity = db.execute('PRAGMA integrity_check').fetchall()
    fk_check  = db.execute('PRAGMA foreign_key_check').fetchall()
    ok = all(row[0] == 'ok' for row in integrity) and len(fk_check) == 0
    return {
        'integrity': [row[0] for row in integrity],
        'fk_violations': len(fk_check),
        'ok': ok,
    }

def getPendingUsers() -> list:
    db = openDB()
    return db.execute(
        'SELECT username, email, lastname, firstname, member_type FROM users WHERE email_verified = 0 ORDER BY id DESC'
    ).fetchall()

def approveUser(username: str) -> bool:
    db = openDB()
    db.execute('UPDATE users SET email_verified = 1, verification_token = NULL WHERE username = ?', (username,))
    db.commit()
    return True

def denyUser(username: str) -> bool:
    db = openDB()
    user = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    if not user:
        return False
    db.execute('DELETE FROM connection_history WHERE user_id = ?', (user['id'],))
    db.execute('DELETE FROM users WHERE username = ?', (username,))
    db.commit()
    return True

def getAdminFullStats() -> dict:
    db = openDB()
    top_users = db.execute('''
        SELECT u.username, COUNT(c.id) as connections, u.level, u.points
        FROM users u LEFT JOIN connection_history c ON c.user_id = u.id
        GROUP BY u.id ORDER BY connections DESC LIMIT 5
    ''').fetchall()
    total_connections = db.execute('SELECT COUNT(*) as cnt FROM connection_history').fetchone()['cnt']
    total_users = db.execute('SELECT COUNT(*) as cnt FROM users').fetchone()['cnt']
    services_by_cat = db.execute(
        'SELECT category, COUNT(*) as cnt FROM services GROUP BY category ORDER BY cnt DESC'
    ).fetchall()
    device_status = db.execute(
        'SELECT status, COUNT(*) as cnt FROM devices GROUP BY status'
    ).fetchall()
    return {
        'top_users': [dict(r) for r in top_users],
        'total_connections': total_connections,
        'total_users': total_users,
        'avg_connections': round(total_connections / total_users, 1) if total_users else 0,
        'services_by_cat': [dict(r) for r in services_by_cat],
        'device_status': {r['status']: r['cnt'] for r in device_status},
    }