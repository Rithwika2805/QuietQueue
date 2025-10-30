from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = "quietqueue_secret_key"

from flask_mail import Mail, Message
import random

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'rithwika.mode@gmail.com'
app.config['MAIL_PASSWORD'] = 'ruym fekc fekp albm'

mail = Mail(app)


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

        # --- Institutional email validation ---
        if not email.endswith("@iiita.ac.in"):
            flash("Please use your institutional email (must end with @iiita.ac.in).")
            return redirect(url_for('register'))

        # --- Password confirmation check ---
        if password != confirm:
            flash("Passwords do not match.")
            return redirect(url_for('register'))

        # --- Check if email already exists ---
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM students WHERE email=%s", [email])
        existing = cur.fetchone()
        cur.close()

        if existing:
            flash("Account already exists.")
            return redirect(url_for('register'))

        # --- Save data temporarily in session ---
        session['temp_registration'] = {
            "roll": roll,
            "name": name,
            "email": email,
            "course": course,
            "semester": semester,
            "password": generate_password_hash(password)
        }

        # --- Generate and send OTP ---
        otp = random.randint(100000, 999999)
        session['register_otp'] = otp

        msg = Message("QuietQueue - Registration OTP Verification",
                      sender="rithwika.mode@gmail.com",
                      recipients=[email])
        msg.body = f"Your OTP for QuietQueue registration is: {otp}"
        mail.send(msg)

        flash("OTP sent to your email! Please verify to complete registration.")
        return redirect(url_for('verify_register_otp'))

    # ✅ Return template only for GET requests
    return render_template('register.html')

# ---------- VERIFY REGISTER OTP ----------
@app.route('/verify-register-otp', methods=['GET', 'POST'])
def verify_register_otp():
    if 'temp_registration' not in session:
        flash("Session expired. Please register again.")
        return redirect(url_for('register'))

    if request.method == 'POST':
        entered_otp = request.form['otp']
        if str(entered_otp) == str(session.get('register_otp')):
            # Insert new user into DB
            data = session['temp_registration']
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO students (roll_number, full_name, email, course, semester, password)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (data['roll'], data['name'], data['email'], data['course'], data['semester'], data['password']))
            mysql.connection.commit()
            cur.close()

            # Clear session data
            session.pop('temp_registration', None)
            session.pop('register_otp', None)

            flash("Registration successful! You can now log in.")
            return redirect(url_for('login'))
        else:
            flash("Invalid OTP. Please try again.")
            return redirect(url_for('verify_register_otp'))

    return render_template('verify-register-otp.html')

# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()

        # Check if email exists in students table
        cur.execute("SELECT * FROM students WHERE email=%s", [email])
        user = cur.fetchone()

        # If not found, check admins table
        if not user:
            cur.execute("SELECT * FROM admins WHERE email=%s", [email])
            admin = cur.fetchone()
            cur.close()

            if admin and check_password_hash(admin['password'], password):
                session['admin_id'] = admin['id']
                session['admin_name'] = admin['full_name']
                session['role'] = 'admin'
                flash('Admin login successful!')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid credentials.')
                return redirect(url_for('login'))

        cur.close()

        # If found in students table
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            session['role'] = 'student' 
            flash('Login successful!')
            return redirect(url_for('student_dashboard'))
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
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM students WHERE email=%s", [email])
        user = cur.fetchone()
        cur.close()

        if not user:
            flash("No account found with that email.")
            return redirect(url_for('forgot_password'))

        otp = random.randint(100000, 999999)
        session['reset_email'] = email
        session['otp'] = otp
        session['otp_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # store current time

        # Send OTP Email
        msg = Message("QuietQueue - OTP Verification",
                      sender="rithwika.mode@gmail.com",
                      recipients=[email])
        msg.body = f"Your OTP for password reset is: {otp}. It will expire in 5 minutes."
        mail.send(msg)

        flash("OTP sent to your email. It will expire in 5 minutes.")
        return redirect(url_for('verify_otp'))

    return render_template('forgot-password.html')

# ---------- VERIFY OTP ----------
@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'reset_email' not in session:
        flash("Session expired. Try again.")
        return redirect(url_for('forgot_password'))

    otp_time_str = session.get('otp_time')
    if otp_time_str:
        otp_time = datetime.strptime(otp_time_str, "%Y-%m-%d %H:%M:%S")
        if datetime.now() - otp_time > timedelta(minutes=5):
            session.pop('otp', None)
            session.pop('otp_time', None)
            flash("OTP expired. Please request a new one.")
            return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        user_otp = request.form['otp']
        if str(user_otp) == str(session.get('otp')):
            session.pop('otp')
            session.pop('otp_time', None)
            return redirect(url_for('reset_password'))
        else:
            flash("Invalid OTP. Try again.")
            return redirect(url_for('verify_otp'))

    return render_template('verify-otp.html')

# ---------- RESET PASSWORD ----------
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_email' not in session:
        flash("Session expired. Try again.")
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_pw = request.form['password']
        confirm_pw = request.form['confirm_password']

        if new_pw != confirm_pw:
            flash("Passwords do not match.")
            return redirect(url_for('reset_password'))

        hashed = generate_password_hash(new_pw)
        cur = mysql.connection.cursor()
        cur.execute("UPDATE students SET password=%s WHERE email=%s", (hashed, session['reset_email']))
        mysql.connection.commit()
        cur.close()
        flash("Password updated successfully.")
        session.pop('reset_email', None)
        return redirect(url_for('login'))

    return render_template('reset-password.html')

# ============================================================
# 🧑‍🎓 STUDENT AREA
# ============================================================

@app.route('/dashboard-student')
def student_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_name = session.get('user_name', 'Student')

    # Fetch latest 3 announcements from database
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM announcements ORDER BY created_at DESC LIMIT 3")
    announcements = cur.fetchall()
    cur.close()

    # Example data for testing (can later fetch from DB)
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

    return render_template(
        'dashboard-student.html',
        user_name=user_name,
        upcoming_booking=upcoming_booking,
        recent_activity=recent_activity,
        announcements=announcements  # ✅ pass real announcements to template
    )

@app.route('/seat-layout')
def seat_layout():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('seat-layout.html', current_date=datetime.now().strftime("%Y-%m-%d"))

# ---------- BOOK SEAT API ----------
@app.route('/api/book-seat', methods=['POST'])
def book_seat():
    if 'user_id' not in session:
        return jsonify({'message': 'Not logged in'}), 401

    data = request.get_json()
    seat_id = data.get('seat_id')
    booking_date = data.get('date')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    zone = data.get('zone')
    user_id = session['user_id']

    cur = mysql.connection.cursor()

    # Check if seat already booked
    cur.execute("""
        SELECT * FROM bookings
        WHERE seat_id=%s AND booking_date=%s
        AND ((start_time <= %s AND end_time > %s)
          OR (start_time < %s AND end_time >= %s)
          OR (start_time >= %s AND end_time <= %s))
    """, (seat_id, booking_date, start_time, start_time, end_time, end_time, start_time, end_time))

    existing = cur.fetchone()
    if existing:
        cur.close()
        return jsonify({'message': 'Seat already booked for the selected time.'}), 409

    # Insert booking
    cur.execute("""
        INSERT INTO bookings (user_id, seat_id, booking_date, start_time, end_time, zone)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (user_id, seat_id, booking_date, start_time, end_time, zone))
    mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'Seat booked successfully!'}), 200

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
    cur.execute("SELECT * FROM bookings WHERE student_id=%s ORDER BY booking_date DESC", [session['user_id']])
    bookings = cur.fetchall()
    cur.close()

    return render_template('history.html', bookings=bookings)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM students WHERE id=%s", [session['user_id']])
    user = cur.fetchone()
    cur.close()

    return render_template('profile.html', user=user)

# ---------- UPDATE PROFILE ----------
@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    full_name = request.form['full_name']
    email = request.form['email']

    cur = mysql.connection.cursor()
    cur.execute("UPDATE students SET full_name=%s, email=%s WHERE id=%s", (full_name, email, session['user_id']))
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
    cur.execute("UPDATE students SET password=%s WHERE id=%s", (hashed, session['user_id']))
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
    cur.execute("UPDATE students SET photo=%s WHERE id=%s", (filename, session['user_id']))
    mysql.connection.commit()
    cur.close()

    flash("Photo uploaded successfully.")
    return redirect(url_for('profile'))

# ============================================================
# 🧑‍💼 ADMIN DASHBOARD
# ============================================================
@app.route('/dashboard-admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash("Access denied. Admins only.")
        return redirect(url_for('login'))

    stats = {
        "total_books": 4521,
        "issued": 215,
        "seats_booked": 12,
        "overdue": 4
    }
    return render_template('dashboard-admin.html', stats=stats)

# ---------- ADMIN PROFILE ----------
@app.route('/admin-profile')
def admin_profile():
    if 'admin_id' not in session:
        flash("Access denied.")
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM admins WHERE id=%s", [session['admin_id']])
    admin = cur.fetchone()
    cur.close()

    return render_template('admin-profile.html', admin=admin)


@app.route('/update-admin-profile', methods=['POST'])
def update_admin_profile():
    if 'admin_id' not in session:
        flash("Access denied.")
        return redirect(url_for('login'))

    full_name = request.form['full_name']
    email = request.form['email']

    cur = mysql.connection.cursor()
    cur.execute("UPDATE admins SET full_name=%s, email=%s WHERE id=%s",
                (full_name, email, session['admin_id']))
    mysql.connection.commit()
    cur.close()

    flash("Profile updated successfully.")
    return redirect(url_for('admin_profile'))


@app.route('/update-admin-password', methods=['POST'])
def update_admin_password():
    if 'admin_id' not in session:
        flash("Access denied.")
        return redirect(url_for('login'))

    new_pw = request.form['new_password']
    confirm_pw = request.form['confirm_password']

    if new_pw != confirm_pw:
        flash("Passwords do not match.")
        return redirect(url_for('admin_profile'))

    hashed_pw = generate_password_hash(new_pw)
    cur = mysql.connection.cursor()
    cur.execute("UPDATE admins SET password=%s WHERE id=%s",
                (hashed_pw, session['admin_id']))
    mysql.connection.commit()
    cur.close()

    flash("Password changed successfully.")
    return redirect(url_for('admin_profile'))

# ============================================================
# 📚 ADMIN - MANAGE BOOKS
# ============================================================

@app.route('/manage-books')
def manage_books():
    if 'admin_id' not in session:
        flash('Access denied.')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM books ORDER BY id DESC")
    books = cur.fetchall()
    cur.close()

    return render_template('manage-books.html', books=books)


# ---------- ADD / UPDATE BOOK ----------
@app.route('/api/add-book', methods=['POST'])
def add_book():
    if 'admin_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized access'}), 403

    data = request.get_json()
    book_id = data.get('id')
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    category = data.get('category')
    total_copies = data.get('total_copies')
    available_copies = data.get('available_copies')

    cur = mysql.connection.cursor()
    if book_id:  # Update
        cur.execute("""
            UPDATE books 
            SET title=%s, author=%s, isbn=%s, category=%s, total_copies=%s, available_copies=%s
            WHERE id=%s
        """, (title, author, isbn, category, total_copies, available_copies, book_id))
    else:  # Add new book
        cur.execute("""
            INSERT INTO books (title, author, isbn, category, total_copies, available_copies)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (title, author, isbn, category, total_copies, available_copies))

    mysql.connection.commit()
    cur.close()
    return jsonify({'status': 'success', 'message': 'Book saved successfully!'})


# ---------- DELETE BOOK ----------
@app.route('/api/delete-book/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    if 'admin_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized access'}), 403

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM books WHERE id=%s", [book_id])
    mysql.connection.commit()
    cur.close()
    return jsonify({'status': 'success', 'message': 'Book deleted successfully!'})

# ---------- MANAGE USERS ----------
@app.route('/manage-users')
def manage_users():
    if 'admin_id' not in session:
        flash('Access denied.')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, roll_number, full_name, email, course, semester FROM students ORDER BY id DESC")
    students = cur.fetchall()
    cur.close()

    return render_template('manage-users.html', students=students)

# ---------- DELETE USER ----------
@app.route('/api/delete-user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if 'admin_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized access'}), 403

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM students WHERE id=%s", [user_id])
    mysql.connection.commit()
    cur.close()

    return jsonify({'status': 'success', 'message': 'User deleted successfully!'})

# ============================================================
# 📢 ADMIN - ANNOUNCEMENTS
# ============================================================

@app.route('/announcements')
def announcements():
    if 'admin_id' not in session:
        flash('Access denied.')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM announcements ORDER BY created_at DESC")
    announcements = cur.fetchall()
    cur.close()

    return render_template('announcements.html', announcements=announcements)


# ---------- ADD ANNOUNCEMENT ----------
@app.route('/api/add-announcement', methods=['POST'])
def add_announcement():
    if 'admin_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized access'}), 403

    data = request.get_json()
    title = data.get('title')
    message = data.get('message')
    created_by = session.get('admin_name', 'Admin')

    if not title or not message:
        return jsonify({'status': 'error', 'message': 'Please fill in all fields.'}), 400

    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO announcements (title, message, created_by) VALUES (%s, %s, %s)",
        (title, message, created_by)
    )
    mysql.connection.commit()
    cur.close()

    return jsonify({'status': 'success', 'message': 'Announcement added successfully!'})


# ---------- DELETE ANNOUNCEMENT ----------
@app.route('/api/delete-announcement/<int:announcement_id>', methods=['DELETE'])
def delete_announcement(announcement_id):
    if 'admin_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized access'}), 403

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM announcements WHERE id=%s", [announcement_id])
    mysql.connection.commit()
    cur.close()

    return jsonify({'status': 'success', 'message': 'Announcement deleted successfully!'})

# ============================================================
# MAIN ENTRY
# ============================================================
if __name__ == '__main__':
    app.run(debug=True)
