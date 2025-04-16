from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
import os
from dotenv import load_dotenv
from uuid import uuid4

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev")  # Replace with a strong secret key in .env

DATABASE_URL = os.environ.get("DATABASE_URL")  # from .env or Render environment

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@app.route('/')
def home():
    if 'user_id' not in session:
        session['user_id'] = str(uuid4())  # create a user ID if not already in session
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (id) VALUES (%s)", (session['user_id'],))
        conn.commit()
        cur.close()
        conn.close()
    return redirect(url_for('submit_task'))

@app.route('/submit', methods=['GET', 'POST'])
def submit_task():
    user_id = session.get('user_id')
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        if not name or not description:
            flash("Please provide both your name and task description!", "warning")
            return redirect(url_for('submit_task'))
        cur.execute(
            "INSERT INTO tasks (name, description, status, user_id) VALUES (%s, %s, %s, %s)",
            (name, description, 'outstanding', user_id)
        )
        conn.commit()
        flash("Task submitted successfully!", "success")
        return redirect(url_for('submit_task'))

    cur.execute("SELECT * FROM tasks WHERE user_id = %s AND status = 'outstanding'", (user_id,))
    tasks = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('submit.html', tasks=tasks)

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE status = 'outstanding'")
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
    cur.execute("UPDATE tasks SET status = 'completed' WHERE id = %s", (task_id,))
    conn.commit()
    cur.close()
    conn.close()
    flash(f"Task #{task_id} marked as completed.", "success")
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == os.environ.get("ADMIN_PASSWORD"):
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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # For Render or local default
    app.run(host='0.0.0.0', port=port)
