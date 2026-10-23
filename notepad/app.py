from pathlib import Path
import sqlite3
from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)
DB_PATH = Path(__file__).resolve().parent / 'notes.db'


def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL
        )''')


@app.get('/')
def index():
    return redirect(url_for('home'))


@app.get('/home')
def home():
    with get_db() as db:
        notes = db.execute('SELECT id, content FROM notes ORDER BY id DESC').fetchall()
    return render_template('home.html', notes=notes)


@app.post('/save')
def save_note():
    content = request.form.get('note', '').strip()
    if content:
        with get_db() as db:
            db.execute('INSERT INTO notes (content) VALUES (?)', (content,))
    return redirect(url_for('home'))


@app.get("/notes")
def view_notes():
    with get_db() as db:
        rows = db.execute(
            "SELECT id, content FROM notes ORDER BY id DESC"
        ).fetchall()

    notes = [dict(row) for row in rows]

    return render_template("notes.html", notes=notes)


@app.get("/api")
def get_notes():
    try:
        with get_db() as db:
            rows = db.execute(
                "SELECT id, content FROM notes ORDER BY id"
            ).fetchall()

        # No notes found
        if not rows:
            return "", 204

        # Notes found
        notes = [dict(row) for row in rows]

        return jsonify({
            "notes": notes
        }), 200

    except Exception:
        app.logger.exception("Failed to retrieve notes")
        return jsonify({
            "error": "Internal server error"
        }), 500


init_db()

if __name__ == '__main__':
    app.run(debug=True)
