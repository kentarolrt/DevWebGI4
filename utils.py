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


def createUser(username: str, password: str) -> tuple[bool, str]:
    db = openDB()

    existing = db.execute(
        'SELECT id FROM users WHERE username = ?', (username,)
    ).fetchone()

    if existing:
        return False, 'username_taken'
    
    db.execute(
        'INSERT INTO users (username, password) VALUES (?, ?)', (username, generate_password_hash(password))
    )

    db.commit()

    return True, 'ok'

def createAdmin(username: str, password: str) -> None:
    db = openDB()
    db.execute(
        'INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)',
        (username, generate_password_hash(password), 'admin')
    )
    db.commit()


    