import sqlite3
import flask
from werkzeug.security import generate_password_hash, check_password_hash

BASE = 'base.db'

def openDB() -> sqlite3.Connection:
    if 'db' not in flask.g:
        flask.g.db = sqlite3.connect(BASE)
        flask.g.db.row_factory = sqlite3.Row
    return flask.g.db


def closeDB(e = None):
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
            nom TEXT,
            prenom TEXT,
            age INTEGER,
            genre TEXT,
            date_naissance TEXT,
            type_membre TEXT,
            photo TEXT,
            niveau TEXT DEFAULT 'debutant',
            points REAL DEFAULT 0,
            email TEXT,
            email_verifie INTEGER DEFAULT 0,
            role TEXT DEFAULT 'simple'
        );

        CREATE TABLE IF NOT EXISTS objets_connectes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            description TEXT,
            type TEXT,
            marque TEXT,
            etat TEXT DEFAULT 'actif',
            connectivite TEXT,
            batterie INTEGER,
            piece TEXT
        );

        CREATE TABLE IF NOT EXISTS historique_connexions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date_connexion TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    ''')

    db.commit()


def createUser(username, password, lastname, firstname, email, age, gender, birthdate) -> tuple[bool, str]:
    db = openDB()

    existing = db.execute(
        'SELECT id FROM users WHERE username = ?', 
        (username,)
    ).fetchone()

    if existing:
        return False, 'username_taken'
    
    db.execute(
        'INSERT INTO users (username, password, nom, prenom, email, age, genre, date_naissance) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (username, generate_password_hash(password), lastname, firstname, email, age, gender, birthdate)
    )

    db.commit()

    return True, 'ok'

def createAdmin(username, password) -> None:
    db = openDB()
    db.execute(
        'INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)',
        (username, generate_password_hash(password), 'admin')
    )
    db.commit()


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

ALLOWED_FIELDS = {'username', 'email', 'nom', 'prenom', 'age', 'genre', 'date_naissance'}

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

def searchObjets(query='', filtre_type='', filtre_etat='') -> list:
    db = openDB()
    
    sql = 'SELECT * FROM objets_connectes WHERE 1=1'
    params = []

    if query:
        sql += ' AND (nom LIKE ? OR description LIKE ?)'
        params.extend([f'%{query}%', f'%{query}%'])

    if filtre_type:
        sql += ' AND type = ?'
        params.append(filtre_type)

    if filtre_etat:
        sql += ' AND etat = ?'
        params.append(filtre_etat)

    sql += ' ORDER BY nom'
    return db.execute(sql, params).fetchall()

def getTypes() -> list:
    db = openDB()
    rows = db.execute('SELECT DISTINCT type FROM objets_connectes ORDER BY type').fetchall()
    return [row['type'] for row in rows]