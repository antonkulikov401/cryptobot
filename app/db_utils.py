from pathlib import Path
import sqlite3


conn = None


def open_connection():
    global conn
    conn = sqlite3.connect(str(Path('./database.db')), check_same_thread=False)


def close_connection():
    global conn
    conn.close()


def create_tables():
    global conn
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            lang VARCHAR(3) NOT NULL,
            currency VARCHAR(3) NOT NULL
        )''')
    conn.commit()


def add_user(cid):
    global conn
    cur = conn.cursor()
    cur.execute('INSERT OR IGNORE INTO users VALUES (?, ?, ?)',
                (str(cid), 'eng', 'usd'))
    conn.commit()


def change_lang(cid, lang):
    global conn
    cur = conn.cursor()
    cur.execute('UPDATE users SET lang = ? WHERE id = ?', (lang, str(cid)))
    conn.commit()


def change_currency(cid, currency):
    global conn
    cur = conn.cursor()
    cur.execute('UPDATE users SET currency = ? WHERE id = ?',
                (currency, str(cid)))
    conn.commit()


def get_lang(cid):
    global conn
    cur = conn.cursor()
    cur.execute('''
        SELECT lang
        FROM users
        WHERE id = ?''', (str(cid),))
    lang = cur.fetchone()
    if lang is None:
        add_user(cid)
    return 'eng' if lang is None else lang[0]


def get_currency(cid):
    global conn
    cur = conn.cursor()
    cur.execute('''
        SELECT currency
        FROM users
        WHERE id = ?''', (str(cid),))
    currency = cur.fetchone()
    if currency is None:
        add_user(cid)
    return 'usd' if currency is None else currency[0]
