from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "quietqueue_secret_key"

# ---------------------------------------------
# 🗄️ MySQL Database Configuration
# ---------------------------------------------
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'quietqueue'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# ---------------------------------------------
# 📁 Upload Folder for Profile Photos
# ---------------------------------------------
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ============================================================
# 👤 AUTHENTICATION ROUTES
# ============================================================

@app.route('/')
def home():
    return redirect(url_for('login'))

# ---------- REGISTER ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        roll = request.form['roll']
        name = request.form['name']
        email = request.form['email']
        course = request.form['course']
        semester = request.form['semester']
        password = request.form['password']
        confirm = request.form['confirm_password']

        if password != confirm:
            flash("Passwords do not match.")
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", [email])
        existing = cur.fetchone()

        if existing:
            flash("Account already exists.")
            cur.close()
            return redirect(url_for('register'))

        cur.execute("""
            INSERT INTO users (roll, name, email, course, semester, password)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (roll, name, email, course, semester, hashed_pw))
        mysql.connection.commit()
        cur.close()

        flash("Registration successful! Please login.")
        return redirect(url_for('login'))

    return render_template('register.html')

# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", [email])
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['is_admin'] = user.get('is_admin', 0)
            flash('Login successful!')
            if session['is_admin']:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.')
            return redirect(url_for('login'))

    return render_template('login.html')

# ---------- LOGOUT ----------
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))

# ---------- FORGOT PASSWORD ----------
@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        email = request.form['email']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", [email])
        user = cur.fetchone()
        cur.close()

        if not user:
            flash("No account found with that email.")
            return redirect(url_for('forgot'))

        session['reset_email'] = email
        return redirect(url_for('reset_password'))

    return render_template('forgot.html')

# ---------- RESET PASSWORD ----------
@app.route('/reset', methods=['GET', 'POST'])
def reset_password():
    if 'reset_email' not in session:
        flash("Session expired. Try again.")
        return redirect(url_for('forgot'))

    if request.method == 'POST':
        new_pw = request.form['password']
        confirm_pw = request.form['confirm_password']

        if new_pw != confirm_pw:
            flash("Passwords do not match.")
            return redirect(url_for('reset_password'))

        hashed = generate_password_hash(new_pw)
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET password=%s WHERE email=%s", (hashed, session['reset_email']))
        mysql.connection.commit()
        cur.close()
        flash("Password updated successfully.")
        session.pop('reset_email', None)
        return redirect(url_for('login'))

    return render_template('reset.html')

# ============================================================
# 🧑‍🎓 STUDENT AREA
# ============================================================

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_name = session.get('user_name', 'Student')

    # Example data (replace with DB queries)
    upcoming_booking = {
        "date": "Oct 30, 2025",
        "time": "10 AM - 12 PM",
        "zone": "Zone 3",
        "seat": "A5"
    }

    recent_activity = [
        "Booked Zone 1 Seat B3",
        "Returned 'Data Structures Made Easy'",
        "Checked availability for Zone 4"
    ]

    notifications = [
        "Library will close early tomorrow (5 PM).",
        "New arrivals in Computer Science section!"
    ]

    return render_template(
        'student_dashboard.html',
        user_name=user_name,
        upcoming_booking=upcoming_booking,
        recent_activity=recent_activity,
        notifications=notifications
    )

@app.route('/seat-layout')
def seat_layout():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('seat-layout.html', current_date=datetime.now().strftime("%Y-%m-%d"))

# ---------- BOOK SEAT API ----------
@app.route('/api/book-seat', methods=['POST'])
def book_seat():
    data = request.get_json()
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"message": "Not logged in"}), 403

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO bookings (user_id, seat_id, date, start_time, end_time)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, data['seat_id'], data['date'], data['start_time'], data['end_time']))
    mysql.connection.commit()
    cur.close()

    return jsonify({"message": "Seat booked successfully!"})

@app.route('/book-search', methods=['GET'])
def book_search():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    q = request.args.get('q', '')
    cur = mysql.connection.cursor()
    if q:
        cur.execute("SELECT * FROM books WHERE title LIKE %s OR isbn LIKE %s", (f"%{q}%", f"%{q}%"))
    else:
        cur.execute("SELECT * FROM books LIMIT 10")
    books = cur.fetchall()
    cur.close()

    filters = [
        {"id": "department", "name": "Department", "options": [
            {"label": "CSE", "value": "CSE"},
            {"label": "ECE", "value": "ECE"},
            {"label": "MECH", "value": "MECH"},
        ]},
        {"id": "availability", "name": "Availability", "options": [
            {"label": "Available", "value": "available"},
            {"label": "On Loan", "value": "loan"},
        ]}
    ]
    return render_template('book-search.html', books=books, search_query=q, filters=filters)

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM bookings WHERE user_id=%s ORDER BY date DESC", [session['user_id']])
    bookings = cur.fetchall()
    cur.close()

    return render_template('history.html', bookings=bookings)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id=%s", [session['user_id']])
    user = cur.fetchone()
    cur.close()

    return render_template('profile.html', user=user)

# ---------- UPDATE PROFILE ----------
@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    name = request.form['name']
    email = request.form['email']

    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET name=%s, email=%s WHERE id=%s", (name, email, session['user_id']))
    mysql.connection.commit()
    cur.close()

    flash("Profile updated successfully.")
    return redirect(url_for('profile'))

# ---------- CHANGE PASSWORD ----------
@app.route('/change-password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    new_pw = request.form['new_password']
    confirm_pw = request.form['confirm_password']
    if new_pw != confirm_pw:
        flash("Passwords do not match.")
        return redirect(url_for('profile'))

    hashed = generate_password_hash(new_pw)
    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET password=%s WHERE id=%s", (hashed, session['user_id']))
    mysql.connection.commit()
    cur.close()
    flash("Password changed successfully.")
    return redirect(url_for('profile'))

# ---------- UPLOAD PHOTO ----------
@app.route('/upload-photo', methods=['POST'])
def upload_photo():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    file = request.files['photo']
    if file.filename == '':
        flash('No file selected.')
        return redirect(url_for('profile'))

    filename = f"user_{session['user_id']}_{file.filename}"
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)

    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET photo=%s WHERE id=%s", (filename, session['user_id']))
    mysql.connection.commit()
    cur.close()

    flash("Photo uploaded successfully.")
    return redirect(url_for('profile'))

# ============================================================
# 🧑‍💼 ADMIN DASHBOARD
# ============================================================
@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('dashboard'))

    stats = {
        "total_books": 4521,
        "issued": 215,
        "seats_booked": 12,
        "overdue": 4
    }
    return render_template('admin-dashboard.html', stats=stats)

# ============================================================
# MAIN ENTRY
# ============================================================
if __name__ == '__main__':
    app.run(debug=True)
