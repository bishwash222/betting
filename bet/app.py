from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_this_later'

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '#19Ai2027', # Replace with your local MySQL password
    'database': 'betting_website'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # Just pass username, no wallet query balance needed!
    return render_template('index.html', username=session['username'])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)
        
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, email, password_hash) 
                VALUES (%s, %s, %s);
            """, (username, email, hashed_password))
            conn.commit()
            return redirect(url_for('login'))
        except Error as e:
            return f"Registration failed: {e}"
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s;", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            return redirect(url_for('home'))
        else:
            return "Invalid username or password."
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/place_bet', methods=['POST'])
def place_bet():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in first.'}), 401
        
    data = request.get_json()
    user_id = session['user_id']
    stake = float(data.get('stake', 0))
    outcome = data.get('outcome')
    event_id = 1 

    if stake < 1:
        return jsonify({'success': False, 'message': 'Please enter a valid amount.'}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Saves everything directly to track who picked what
        cursor.execute("""
            INSERT INTO bets (user_id, event_id, prediction, stake) 
            VALUES (%s, %s, %s, %s);
        """, (user_id, event_id, outcome, stake))
        
        conn.commit()
        return jsonify({
            'success': True,
            'message': f'Locked in! You placed {stake} points on {outcome}.'
        })
    except Error as e:
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)