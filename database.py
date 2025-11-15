import sqlite3
from datetime import datetime

DB_NAME = 'chatbot.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_user(name, email, password):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                   (name, email, password))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id

def get_user(email):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_user_profile(user_id, name):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET name = ? WHERE id = ?', (name, user_id))
    conn.commit()
    conn.close()

def add_message(user_id, user_message, bot_response):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (user_id, user_message, bot_response) VALUES (?, ?, ?)',
                   (user_id, user_message, bot_response))
    conn.commit()
    conn.close()

def get_user_messages(user_id, limit=50):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_message, bot_response, created_at 
        FROM messages 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
    ''', (user_id, limit))
    messages = cursor.fetchall()
    conn.close()
    return [dict(msg) for msg in messages]