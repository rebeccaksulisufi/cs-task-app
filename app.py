from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure key in production

# Set your admin password here
ADMIN_PASSWORD = 'mypassword'  # Change this to your desired password

DATABASE = 'tasks.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Create the tasks table if it doesn't exist
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'outstanding'
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database on startup
init_db()

@app.route('/')
def home():
    return redirect(url_for('submit_task'))

# Public route: submit a new task and view outstanding tasks
@app.route('/submit', methods=['GET', 'POST'])
def submit_task():
    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        if not name or not description:
            flash("Please provide both your name and task description!", "warning")
            return redirect(url_for('submit_task'))
        conn.execute('INSERT INTO tasks (name, description, status) VALUES (?, ?, ?)',
                     (name, description, 'outstanding'))
        conn.commit()
        flash("Task submitted successfully!", "success")
        return redirect(url_for('submit_task'))
    
    tasks = conn.execute('SELECT * FROM tasks WHERE status="outstanding"').fetchall()
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
    tasks = conn.execute('SELECT * FROM tasks WHERE status="outstanding"').fetchall()
    conn.close()
    return render_template('dashboard.html', tasks=tasks)

# Mark a task as complete (only accessible if logged in)
@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('UPDATE tasks SET status="completed" WHERE id=?', (task_id,))
    conn.commit()
    conn.close()
    flash(f"Task #{task_id} marked as completed.", "success")
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    # When running locally, debug=True
    app.run(host='0.0.0.0', port=5000, debug=True)
