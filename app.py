from flask import Flask, render_template, request, redirect, url_for, session, flash
from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure key in production

# Set your admin password here
ADMIN_PASSWORD = 'mypassword'  # Change this to your desired password


def get_db_connection():
    conn = connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

@app.route('/')
def home():
    return redirect(url_for('submit_task'))

# Public route: submit a new task and view outstanding tasks
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

        cur.execute('INSERT INTO tasks (name, description, status) VALUES (%s, %s, %s)',
                    (name, description, 'outstanding'))
        conn.commit()
        flash("Task submitted successfully!", "success")
        cur.close()
        conn.close()
        return redirect(url_for('submit_task'))

    cur.execute('SELECT * FROM tasks WHERE status = %s', ('outstanding',))
    tasks = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('submit.html', tasks=tasks)

# Login route for the dashboard
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash("Logged in successfully!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Incorrect password, try again.", "danger")
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))

# Dashboard: password-protected view for managing tasks
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM tasks WHERE status = %s', ('outstanding',))
    tasks = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('dashboard.html', tasks=tasks)

# Mark a task as complete (only accessible if logged in)
@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
