from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

DATABASE_URL = os.getenv("DATABASE_URL")

# Connect to database
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

@app.before_request
def create_user_if_not_exists():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE id = %s", (session['user_id'],))
        if not cur.fetchone():
            placeholder_email = f"guest_{session['user_id']}@example.com"
            cur.execute("INSERT INTO users (id, email) VALUES (%s, %s)", (session['user_id'], placeholder_email))
            conn.commit()
        cur.close()
        conn.close()

@app.route('/')
def home():
    return redirect(url_for('submit_task'))

@app.route('/submit', methods=['GET', 'POST'])
def submit_task():
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        if not name or not description:
            flash("Please provide both your name and task description!", "warning")
            return redirect(url_for('submit_task'))
        cur.execute('INSERT INTO tasks (name, description, status, user_id) VALUES (%s, %s, %s, %s)',
                    (name, description, 'outstanding', session['user_id']))
        conn.commit()
        flash("Task submitted successfully!", "success")
        return redirect(url_for('submit_task'))

    cur.execute('SELECT * FROM tasks WHERE status = %s AND user_id = %s', ('outstanding', session['user_id']))
    tasks = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('submit.html', tasks=tasks)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == os.getenv("ADMIN_PASSWORD"):
            session['logged_in'] = True
            flash("Logged in successfully!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Incorrect password, try again.", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM tasks WHERE status = %s AND user_id = %s', ('outstanding', session['user_id']))
    tasks = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('dashboard.html', tasks=tasks)

@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE tasks SET status = %s WHERE id = %s AND user_id = %s', ('completed', task_id, session['user_id']))
    conn.commit()
    cur.close()
    conn.close()
    flash(f"Task #{task_id} marked as completed.", "success")
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
