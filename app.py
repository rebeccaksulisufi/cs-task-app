from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
import os
import uuid
import psycopg2

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")

# Create a database connection
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# Ensure a user is created for session if not already
@app.before_request
def create_user_if_not_exists():
    if 'user_id' not in session:
        user_id = str(uuid.uuid4())
        session['user_id'] = user_id

        # Create placeholder user
        conn = get_db_connection()
        cur = conn.cursor()
        placeholder_email = f"guest_{user_id}@example.com"
        placeholder_password = "guest"  # Default guest password
        cur.execute(
            "INSERT INTO users (id, email, password) VALUES (%s, %s, %s)",
            (user_id, placeholder_email, placeholder_password)
        )
        conn.commit()
        cur.close()
        conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email = %s AND password = %s", (email, password))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session['user_id'] = user[0]
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
