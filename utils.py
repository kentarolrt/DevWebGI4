import sqlite3
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

    db.execute(
        'INSERT INTO users (username, password, lastname, firstname, email, age, gender, birthdate, member_type, role, level) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (username, generate_password_hash(password), lastname, firstname, email, age, gender, birthdate, member_type, role, level)
    )

    db.commit()

    return True, 'ok'


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

def searchDevices(query='', filter_type='', filter_status='') -> list:
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

    sql += ' ORDER BY name'
    return db.execute(sql, params).fetchall()

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

def _computeLevel(points: float) -> str:
    if points < 5:
        return 'debutant'
    elif points < 15:
        return 'intermediaire'
    elif points < 30:
        return 'avance'
    else:
        return 'expert'

def addPoints(username: str, amount: float) -> None:
    db = openDB()
    db.execute('UPDATE users SET points = points + ? WHERE username = ?', (amount, username))
    db.commit()

def upgradeLevel(username: str) -> tuple[bool, str]:
    db = openDB()
    user = db.execute('SELECT points, level FROM users WHERE username = ?', (username,)).fetchone()
    if not user:
        return False, 'user_not_found'
    new_level = _computeLevel(user['points'])
    levels = ['debutant', 'intermediaire', 'avance', 'expert']
    if levels.index(new_level) <= levels.index(user['level']):
        return False, 'not_enough_points'
    db.execute('UPDATE users SET level = ? WHERE username = ?', (new_level, username))
    db.commit()
    return True, new_level

def recordConnection(username: str) -> None:
    db = openDB()
    user = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    if user:
        db.execute('INSERT INTO connection_history (user_id) VALUES (?)', (user['id'],))
        db.commit()
    addPoints(username, 0.25)

def getDevice(device_id: int):
    db = openDB()
    return db.execute('SELECT * FROM devices WHERE id = ?', (device_id,)).fetchone()

def getAllMembers() -> list:
    db = openDB()
    return db.execute(
        'SELECT username, age, gender, birthdate, member_type, level, points FROM users ORDER BY member_type, username'
    ).fetchall()

def deleteUser(username: str) -> tuple[bool, str]:
    db = openDB()
    user = db.execute('SELECT id, role FROM users WHERE username = ?', (username,)).fetchone()
    if not user:
        return False, 'user_not_found'
    db.execute('DELETE FROM connection_history WHERE user_id = ?', (user['id'],))
    db.execute('DELETE FROM users WHERE username = ?', (username,))
    db.commit()
    return True, 'ok'