from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
from datetime import datetime, timedelta, date, time as dtime
import os
import MySQLdb.cursors
from apscheduler.schedulers.background import BackgroundScheduler

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

# ---------- MySQL Database Configuration ----------
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'quietqueue'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# ---------- Upload Folder for Profile Photos ----------
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---------- AUTHENTICATION ROUTES ----------
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

    # Return template only for GET requests
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

# ---------- STUDENT AREA ----------

import MySQLdb.cursors
from datetime import datetime, timedelta, time

@app.route('/dashboard-student')
def student_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user_name = session.get('user_name', 'Student')

    cancel_expired_reservations()
    auto_checkout_expired_bookings()

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch upcoming booking
    cur.execute("""
        SELECT id, seat_id, zone, booking_date, start_time, end_time, status
        FROM bookings
        WHERE user_id=%s
          AND status IN ('reserved', 'checked_in')
          AND TIMESTAMP(booking_date, end_time) > NOW()
        ORDER BY TIMESTAMP(booking_date, start_time)
        LIMIT 1
    """, [user_id])
    upcoming_booking = cur.fetchone()

    if upcoming_booking:
        booking_date = upcoming_booking['booking_date']
        start_time = upcoming_booking['start_time']
        end_time = upcoming_booking['end_time']

        if isinstance(start_time, timedelta):
            start_time = (datetime.min + start_time).time()
        if isinstance(end_time, timedelta):
            end_time = (datetime.min + end_time).time()

        upcoming_booking['booking_date_str'] = booking_date.strftime('%b %d, %Y')
        upcoming_booking['start_time_str'] = start_time.strftime('%I:%M %p')
        upcoming_booking['end_time_str'] = end_time.strftime('%I:%M %p')

    # Fetch recent activity
    cur.execute("""
        SELECT CONCAT('Seat ', seat_id, ' in ', zone, ' from ', start_time, ' to ', end_time, ' (', status, ')') AS activity
        FROM bookings
        WHERE user_id=%s
        ORDER BY id DESC
        LIMIT 3
    """, [user_id])
    recent_activity_rows = cur.fetchall()
    recent_activity = [r['activity'] for r in recent_activity_rows]

    # Fetch announcements
    cur.execute("""
        SELECT a.id, a.title, a.message, a.created_at, ad.full_name AS created_by
        FROM announcements a
        JOIN admins ad ON a.created_by = ad.id
        ORDER BY a.created_at DESC
        LIMIT 3
    """)
    announcements = cur.fetchall()

    cur.close()

    return render_template(
        'dashboard-student.html',
        user_name=user_name,
        upcoming_booking=upcoming_booking,
        recent_activity=recent_activity,
        announcements=announcements
    )

# ---------- STUDENT CHECK-OUT ----------
@app.route('/api/checkout', methods=['POST'])
def student_checkout():
    """
    Allows a student to check out early.
    Updates booking status and frees the seat.
    """
    if 'user_id' not in session:
        return jsonify({'message': 'Login required'}), 401

    student_id = session['user_id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Find the current active booking
    cur.execute("""
        SELECT id, seat_id, zone, status
        FROM bookings
        WHERE user_id = %s AND status = 'checked_in'
        ORDER BY booking_date DESC, start_time DESC
        LIMIT 1
    """, [student_id])
    booking = cur.fetchone()

    if not booking:
        cur.close()
        return jsonify({'message': 'No active booking found to check out.'}), 404

    cur.execute("""
        UPDATE bookings
        SET status = 'checked_out', end_time = NOW()
        WHERE id = %s
    """, [booking['id']])

    cur.execute("""
        UPDATE seats
        SET is_booked = 0, booked_by = NULL, booked_at = NULL
        WHERE seat_number = %s
    """, [booking['seat_id']])

    mysql.connection.commit()
    cur.close()

    return jsonify({'message': f'Checked out successfully from seat {booking["seat_id"]}.'}), 200

@app.route('/seat-layout')
def seat_layout():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('seat-layout.html', current_date=datetime.now().strftime("%Y-%m-%d"))

MAX_DURATION_MINUTES = 180
MIN_DURATION_MINUTES = 60
CHECKIN_GRACE_MINUTES = 20  # booking must be checked-in within 20 minutes of start_time

def dt_from_date_time(booking_date: str, t: str):
    """
    Convert booking_date (YYYY-MM-DD) and time string HH:MM (or HH:MM:SS) to a datetime.
    """
    if t == '24:00' or t == '24:00:00':
        bd = datetime.strptime(booking_date, "%Y-%m-%d").date() + timedelta(days=1)
        return datetime.combine(bd, dtime(0, 0))
    fmt = "%H:%M:%S" if len(t.split(':')) == 3 else "%H:%M"
    bd = datetime.strptime(booking_date, "%Y-%m-%d").date()
    tm = datetime.strptime(t, fmt).time()
    return datetime.combine(bd, tm)

def cancel_expired_reservations():
    """
    Marks bookings as 'cancelled' if they are still 'reserved' and 
    more than 20 minutes past their start time.
    Also sends an email notification to the user when this happens.
    """
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Find all bookings that should be cancelled
    cur.execute("""
        SELECT b.id, b.user_id, b.seat_id, b.zone, b.booking_date, b.start_time, b.end_time,
               s.email, s.full_name
        FROM bookings b
        JOIN students s ON b.user_id = s.id
        WHERE b.status = 'reserved'
          AND (TIMESTAMP(b.booking_date, b.start_time) + INTERVAL %s MINUTE) < NOW()
    """, (CHECKIN_GRACE_MINUTES,))
    expired_bookings = cur.fetchall()

    if expired_bookings:
        cur.execute("""
            UPDATE bookings
            SET status = 'cancelled'
            WHERE status = 'reserved'
              AND (TIMESTAMP(booking_date, start_time) + INTERVAL %s MINUTE) < NOW()
        """, (CHECKIN_GRACE_MINUTES,))
        mysql.connection.commit()

        for booking in expired_bookings:
            try:
                msg = Message(
                    "QuietQueue Booking Cancelled - Check-in Time Missed",
                    sender="rithwika.mode@gmail.com",
                    recipients=[booking['email']]
                )
                msg.body = (
                    f"Hello {booking['full_name']},\n\n"
                    f"Your booking for seat {booking['seat_id']} in zone {booking['zone']} "
                    f"on {booking['booking_date'].strftime('%b %d, %Y')} "
                    f"from {booking['start_time']} to {booking['end_time']} "
                    f"has been automatically cancelled because you did not check in "
                    f"within {CHECKIN_GRACE_MINUTES} minutes of your start time.\n\n"
                    f"If you still wish to use a seat, please make a new booking.\n\n"
                    f"— QuietQueue Team"
                )
                mail.send(msg)
            except Exception as e:
                print(f"Failed to send cancellation email to {booking['email']}: {e}")

    cur.close()

# ---------- AUTO CHECKOUT FOR EXPIRED BOOKINGS ----------
def auto_checkout_expired_bookings():
    """
    Automatically checks out students whose end_time has passed.
    Frees up their seats.
    """
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    now = datetime.now().strftime("%H:%M:%S")
    today = datetime.now().strftime("%Y-%m-%d")

    cur.execute("""
        SELECT id, seat_id, zone
        FROM bookings
        WHERE booking_date = %s
          AND end_time < %s
          AND status = 'checked_in'
    """, (today, now))
    expired = cur.fetchall()

    if expired:
        for b in expired:
            cur.execute("""
                UPDATE bookings
                SET status = 'checked_out'
                WHERE id = %s
            """, [b['id']])

            cur.execute("""
                UPDATE seats
                SET is_booked = 0, booked_by = NULL, booked_at = NULL
                WHERE seat_number = %s
            """, [b['seat_id']])

        mysql.connection.commit()

    cur.close()

def scheduled_cancels():
    with app.app_context():
        try:
            cancel_expired_reservations()
            auto_checkout_expired_bookings()
        except Exception as e:
            print("Error in scheduled cancellation job:", e)

def overlapping_clause_params(start_dt, end_dt):
    """
    returns SQL clause to check overlapping intervals and param order
    Overlap test:
      (start1 < end2) AND (start2 < end1)
    We'll compute TIMESTAMP(booking_date, start_time) comparisons in SQL.
    """
    return """
    WHERE booking_date = %s
      AND status IN ('reserved','checked_in')
      AND (TIMESTAMP(booking_date, start_time) < %s)
      AND (%s < TIMESTAMP(booking_date, end_time))
    """, (start_dt.date().isoformat(), end_dt, start_dt)

# ---------- BOOK SEAT API ----------
@app.route('/api/book-seat', methods=['POST'])
def book_seat():
    if 'user_id' not in session:
        return jsonify({'message': 'Not logged in'}), 401

    cancel_expired_reservations()
    auto_checkout_expired_bookings()

    data = request.get_json() or {}
    seat_id = data.get('seat_id')
    booking_date = data.get('date')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    zone = data.get('zone')
    user_id = session['user_id']

    if not all([seat_id, booking_date, start_time, end_time]):
        return jsonify({'message': 'Missing booking parameters.'}), 400

    try:
        start_dt = dt_from_date_time(booking_date, start_time)
        end_dt = dt_from_date_time(booking_date, end_time)
    except Exception as e:
        return jsonify({'message': 'Invalid date/time format.'}), 400

    # duration validation
    duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
    if duration_minutes <= 0:
        return jsonify({'message': 'End time must be after start time.'}), 400
    if duration_minutes < MIN_DURATION_MINUTES or duration_minutes > MAX_DURATION_MINUTES:
        return jsonify({'message': f'Invalid slot length. Min {MIN_DURATION_MINUTES//60} hr, Max {MAX_DURATION_MINUTES//60} hr.'}), 400

    # ensure booking start is not in the past
    if start_dt < datetime.now():
        return jsonify({'message': 'Cannot create bookings in the past.'}), 400

    cur = mysql.connection.cursor()

    # Check seat availability
    cur.execute("""
        SELECT * FROM bookings
        WHERE seat_id=%s AND booking_date=%s
          AND status IN ('reserved','checked_in')
          AND (TIMESTAMP(booking_date, start_time) < %s) AND (%s < TIMESTAMP(booking_date, end_time))
    """, (seat_id, booking_date, end_dt, start_dt))
    seat_conflict = cur.fetchone()
    if seat_conflict:
        cur.close()
        return jsonify({'message': 'Seat already booked for the selected time.'}), 409

    # Check user doesn't have overlapping booking
    cur.execute("""
        SELECT * FROM bookings
        WHERE user_id=%s AND booking_date=%s
          AND status IN ('reserved','checked_in')
          AND (TIMESTAMP(booking_date, start_time) < %s) AND (%s < TIMESTAMP(booking_date, end_time))
    """, (user_id, booking_date, end_dt, start_dt))
    user_conflict = cur.fetchone()
    if user_conflict:
        cur.close()
        return jsonify({'message': 'You already have a booking that overlaps this time.'}), 409

    # Insert booking as 'reserved'
    cur.execute("""
        INSERT INTO bookings (user_id, seat_id, booking_date, start_time, end_time, zone, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'reserved')
    """, (user_id, seat_id, booking_date, start_time, end_time, zone))
    mysql.connection.commit()
    booking_id = cur.lastrowid
    cur.close()

    # Return booking id
    return jsonify({
        'message': 'Seat reserved successfully. Please check-in within 20 minutes of the start time to confirm.',
        'booking_id': booking_id
    }), 200

# ---------- CHECK-IN API ----------
@app.route('/api/check-in', methods=['POST'])
def check_in():
    """
    Call this when the user arrives to mark the reservation as checked_in.
    Rules:
    - Only the user who owns the booking may check-in.
    - Check-in must occur at or after booking start_time and before start_time + CHECKIN_GRACE_MINUTES.
    """
    if 'user_id' not in session:
        return jsonify({'message': 'Not logged in'}), 401

    data = request.get_json() or {}
    booking_id = data.get('booking_id')
    if not booking_id:
        return jsonify({'message': 'booking_id required'}), 400

    # cancel expired reservations first
    cancel_expired_reservations()
    auto_checkout_expired_bookings()

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM bookings WHERE id=%s", [booking_id])
    booking = cur.fetchone()
    if not booking:
        cur.close()
        return jsonify({'message': 'Booking not found.'}), 404

    if booking['user_id'] != session['user_id']:
        cur.close()
        return jsonify({'message': 'Unauthorized.'}), 403

    if booking['status'] != 'reserved':
        cur.close()
        return jsonify({'message': f'Booking cannot be checked-in (status: {booking["status"]}).'}), 400

    # time window check
    start_dt = datetime.combine(booking['booking_date'], booking['start_time'])
    now = datetime.now()
    if now < start_dt:
        if (start_dt - now).total_seconds() > (60 * 30):
            cur.close()
            return jsonify({'message': 'Too early to check-in. Please come within 30 minutes of your booking start.'}), 400

    if now > (start_dt + timedelta(minutes=CHECKIN_GRACE_MINUTES)):
        cur.execute("UPDATE bookings SET status='cancelled' WHERE id=%s", [booking_id])
        mysql.connection.commit()
        cur.close()
        return jsonify({'message': 'Booking has expired and been cancelled.'}), 400

    # mark checked_in
    cur.execute("UPDATE bookings SET status='checked_in', checked_in_at=NOW() WHERE id=%s", [booking_id])
    mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'Checked-in successfully. Enjoy your slot!'}), 200

# ---------- ADMIN CHECK-IN API ----------
@app.route('/api/admin/check-in', methods=['POST'])
def admin_check_in():
    """
    Allows admin to check-in a student manually when they arrive.
    - Only admin users can perform this action.
    - Booking must exist and be in 'reserved' state.
    - Must be within 20 minutes after booking start.
    """
    if 'admin_id' not in session:
        return jsonify({'message': 'Admin login required'}), 401

    data = request.get_json() or {}
    booking_id = data.get('booking_id')
    if not booking_id:
        return jsonify({'message': 'booking_id required'}), 400

    cancel_expired_reservations()
    auto_checkout_expired_bookings()

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM bookings WHERE id=%s", [booking_id])
    booking = cur.fetchone()
    if not booking:
        cur.close()
        return jsonify({'message': 'Booking not found'}), 404

    if booking['status'] != 'reserved':
        cur.close()
        return jsonify({'message': f'Booking already {booking["status"]}.'}), 400

    start_dt = datetime.combine(booking['booking_date'], booking['start_time'])
    now = datetime.now()

    if now < (start_dt - timedelta(minutes=30)):
        cur.close()
        return jsonify({'message': 'Too early to check-in. Please wait until within 30 minutes of start time.'}), 400

    if now > (start_dt + timedelta(minutes=CHECKIN_GRACE_MINUTES)):
        cur.execute("UPDATE bookings SET status='cancelled' WHERE id=%s", [booking_id])
        mysql.connection.commit()
        cur.close()
        return jsonify({'message': 'Booking expired and has been cancelled.'}), 400

    cur.execute("""
        UPDATE bookings
        SET status='checked_in', checked_in_at=NOW()
        WHERE id=%s
    """, [booking_id])
    mysql.connection.commit()
    cur.close()

    return jsonify({'message': f"Booking ID {booking_id} checked in successfully!"}), 200

# ---------- CANCEL BOOKING API ----------
@app.route('/api/cancel-booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT id, status 
            FROM bookings 
            WHERE id = %s AND user_id = %s AND status IN ('reserved','checked_in')
        """, [booking_id, session['user_id']])
        booking = cur.fetchone()

        if not booking:
            cur.close()
            return jsonify({'message': 'No active booking found'}), 404

        cur.execute("""
            UPDATE bookings 
            SET status = 'cancelled' 
            WHERE id = %s
        """, [booking_id])
        mysql.connection.commit()
        cur.close()

        return jsonify({'message': 'Booking cancelled successfully'}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/my-booking')
def my_booking():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    user_id = session['user_id']
    seat_id = request.args.get('seat_id')      
    booking_date = request.args.get('booking_date') 

    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        if seat_id and booking_date:
            cur.execute("""
                SELECT id AS booking_id, seat_id, zone, booking_date, start_time, end_time, status
                FROM bookings
                WHERE user_id=%s
                  AND seat_id=%s
                  AND booking_date=%s
                  AND status IN ('reserved','checked_in')
                LIMIT 1
            """, [user_id, seat_id, booking_date])
            booking = cur.fetchone()
            if booking:
                cur.close()
                if booking['booking_date']:
                    booking['booking_date'] = booking['booking_date'].strftime('%Y-%m-%d')
                from datetime import timedelta
                if isinstance(booking['start_time'], timedelta):
                    total = booking['start_time'].total_seconds()
                    booking['start_time'] = f"{int(total//3600):02d}:{int((total%3600)//60):02d}:00"
                if isinstance(booking['end_time'], timedelta):
                    total = booking['end_time'].total_seconds()
                    booking['end_time'] = f"{int(total//3600):02d}:{int((total%3600)//60):02d}:00"
                return jsonify(booking)

        if booking_date:
            cur.execute("""
                SELECT id AS booking_id, seat_id, zone, booking_date, start_time, end_time, status
                FROM bookings
                WHERE user_id=%s
                  AND booking_date=%s
                  AND status IN ('reserved','checked_in')
                ORDER BY start_time ASC
                LIMIT 1
            """, [user_id, booking_date])
            booking = cur.fetchone()
            if booking:
                cur.close()
                if booking['booking_date']:
                    booking['booking_date'] = booking['booking_date'].strftime('%Y-%m-%d')
                from datetime import timedelta
                if isinstance(booking['start_time'], timedelta):
                    total = booking['start_time'].total_seconds()
                    booking['start_time'] = f"{int(total//3600):02d}:{int((total%3600)//60):02d}:00"
                if isinstance(booking['end_time'], timedelta):
                    total = booking['end_time'].total_seconds()
                    booking['end_time'] = f"{int(total//3600):02d}:{int((total%3600)//60):02d}:00"
                return jsonify(booking)

        if seat_id:
            cur.execute("""
                SELECT id AS booking_id, seat_id, zone, booking_date, start_time, end_time, status
                FROM bookings
                WHERE user_id=%s
                  AND seat_id=%s
                  AND status IN ('reserved','checked_in')
                ORDER BY booking_date ASC, start_time ASC
                LIMIT 1
            """, [user_id, seat_id])
            booking = cur.fetchone()
            if booking:
                cur.close()
                if booking['booking_date']:
                    booking['booking_date'] = booking['booking_date'].strftime('%Y-%m-%d')
                from datetime import timedelta
                if isinstance(booking['start_time'], timedelta):
                    total = booking['start_time'].total_seconds()
                    booking['start_time'] = f"{int(total//3600):02d}:{int((total%3600)//60):02d}:00"
                if isinstance(booking['end_time'], timedelta):
                    total = booking['end_time'].total_seconds()
                    booking['end_time'] = f"{int(total//3600):02d}:{int((total%3600)//60):02d}:00"
                return jsonify(booking)

        cur.execute("""
            SELECT id AS booking_id, seat_id, zone, booking_date, start_time, end_time, status
            FROM bookings
            WHERE user_id=%s
              AND status IN ('reserved','checked_in')
              AND TIMESTAMP(booking_date, end_time) > NOW()
            ORDER BY TIMESTAMP(booking_date, start_time) ASC
            LIMIT 1
        """, [user_id])
        booking = cur.fetchone()
        if booking:
            cur.close()
            if booking['booking_date']:
                booking['booking_date'] = booking['booking_date'].strftime('%Y-%m-%d')
            from datetime import timedelta
            if isinstance(booking['start_time'], timedelta):
                total = booking['start_time'].total_seconds()
                booking['start_time'] = f"{int(total//3600):02d}:{int((total%3600)//60):02d}:00"
            if isinstance(booking['end_time'], timedelta):
                total = booking['end_time'].total_seconds()
                booking['end_time'] = f"{int(total//3600):02d}:{int((total%3600)//60):02d}:00"
            return jsonify(booking)

        cur.execute("""
            SELECT id AS booking_id, seat_id, zone, booking_date, start_time, end_time, status
            FROM bookings
            WHERE user_id=%s
              AND status IN ('reserved','checked_in')
            ORDER BY booking_date DESC, id DESC
            LIMIT 1
        """, [user_id])
        booking = cur.fetchone()
        cur.close()
        if not booking:
            return jsonify({})
        if booking['booking_date']:
            booking['booking_date'] = booking['booking_date'].strftime('%Y-%m-%d')
        from datetime import timedelta
        if isinstance(booking['start_time'], timedelta):
            total = booking['start_time'].total_seconds()
            booking['start_time'] = f"{int(total//3600):02d}:{int((total%3600)//60):02d}:00"
        if isinstance(booking['end_time'], timedelta):
            total = booking['end_time'].total_seconds()
            booking['end_time'] = f"{int(total//3600):02d}:{int((total%3600)//60):02d}:00"
        return jsonify(booking)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/booked-seats', methods=['GET'])
def booked_seats():
    """
    Returns seats booked during the selected date & time:
    - 'R' = reserved/checked-in by others (red)
    - 'B' = booked by current user (blue)
    """
    if 'user_id' not in session:
        return jsonify([]), 401

    user_id = session['user_id']
    date = request.args.get('date')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    zone = request.args.get('zone')  # optional filter

    if not (date and start_time and end_time):
        return jsonify({'message': 'Missing parameters'}), 400

    try:
        start_dt = dt_from_date_time(date, start_time)
        end_dt = dt_from_date_time(date, end_time)
    except Exception:
        return jsonify({'message': 'Invalid time format'}), 400

    cancel_expired_reservations()
    auto_checkout_expired_bookings()

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    zone_filter = "AND zone = %s" if zone else ""
    params = [date, end_dt, start_dt] if not zone else [date, zone, end_dt, start_dt]

    cur.execute(f"""
        SELECT seat_id, user_id
        FROM bookings
        WHERE booking_date=%s
          {zone_filter}
          AND status IN ('reserved', 'checked_in')
          AND (TIMESTAMP(booking_date, start_time) < %s)
          AND (%s < TIMESTAMP(booking_date, end_time))
    """, params)

    all_rows = cur.fetchall()
    cur.close()

    result = []
    for r in all_rows:
        result.append({
            "seat_id": r['seat_id'],
            "status": "B" if r['user_id'] == user_id else "R"
        })

    return jsonify(result)

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
            {"label": "IT", "value": "IT"},
            {"label": "ECE", "value": "ECE"},
            {"label": "IT-BI", "value": "IT-BI"},
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

    user_id = session['user_id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch upcoming bookings
    cur.execute("""
        SELECT * FROM bookings
        WHERE user_id = %s
          AND TIMESTAMP(booking_date, start_time) >= NOW()
        ORDER BY booking_date ASC, start_time ASC
    """, [user_id])
    future_bookings = cur.fetchall()

    # Fetch 2 previous bookings
    cur.execute("""
        SELECT * FROM bookings
        WHERE user_id = %s
        AND (
            TIMESTAMP(booking_date, end_time) < NOW()
            OR status = 'cancelled'
        )
        ORDER BY booking_date DESC, end_time DESC
        LIMIT 2
    """, [user_id])
    past_bookings = cur.fetchall()
    cur.close()

    def safe_convert_time(t):
        if isinstance(t, timedelta):
            total_seconds = int(t.total_seconds())
            hours = (total_seconds // 3600) % 24
            minutes = (total_seconds % 3600) // 60
            return dtime(hour=hours, minute=minutes)
        return t

    for group in (future_bookings, past_bookings):
        for booking in group:
            booking['start_time'] = safe_convert_time(booking['start_time'])
            booking['end_time'] = safe_convert_time(booking['end_time'])
            # Ensure booking_date is a datetime.date
            if isinstance(booking['booking_date'], datetime):
                booking['booking_date'] = booking['booking_date'].date()

    return render_template(
        'history.html',
        future_bookings=future_bookings,
        past_bookings=past_bookings
    )

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

# ---------- CONTACT US ----------
@app.route('/contact', methods=['GET'])
def contact():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_name = session.get('user_name', 'Student')
    return render_template('contact.html', user_name=user_name)

@app.route('/send-contact', methods=['POST'])
def send_contact():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    name = request.form['name']
    email = request.form['email']
    message = request.form['message']

    try:
        msg = Message(
            subject=f"New Contact Message from {name}",
            sender="rithwika.mode@gmail.com",
            recipients=["rithwika.mode@gmail.com"]
        )
        msg.body = f"From: {name} <{email}>\n\nMessage:\n{message}"
        mail.send(msg)
        flash("Your message has been sent successfully!")
    except Exception as e:
        print("Error sending contact message:", e)
        flash("Failed to send your message. Please try again later.")

    return redirect(url_for('contact'))

# ---------- ADMIN DASHBOARD ----------
@app.route('/dashboard-admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash("Access denied. Admins only.")
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM admins WHERE id = %s", (session['admin_id'],))
    admin = cur.fetchone()
    cur.close()

    return render_template('dashboard-admin.html', current_date=datetime.now().strftime("%Y-%m-%d"), admin=admin)

@app.route('/api/admin/reserved-bookings')
def get_reserved_bookings():
    """Return today's reserved seat bookings for admin check-in panel."""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    cancel_expired_reservations()
    auto_checkout_expired_bookings()

    date = request.args.get('date') or datetime.now().strftime('%Y-%m-%d')

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT b.id, b.seat_id, b.zone, b.start_time, b.end_time, b.status,
               s.full_name AS name, s.roll_number AS roll_no, s.email
        FROM bookings b
        JOIN students s ON b.user_id = s.id
        WHERE b.booking_date = %s
          AND b.status IN ('reserved','checked_in')
        ORDER BY b.start_time ASC
    """, (date,))
    bookings = cur.fetchall()
    cur.close()

    for b in bookings:
        from datetime import timedelta
        if isinstance(b['start_time'], timedelta):
            total = int(b['start_time'].total_seconds())
            b['start_time'] = f"{total//3600:02d}:{(total%3600)//60:02d}"
        if isinstance(b['end_time'], timedelta):
            total = int(b['end_time'].total_seconds())
            b['end_time'] = f"{total//3600:02d}:{(total%3600)//60:02d}"

    return jsonify({'bookings': bookings})

# ---------- ADMIN MANUAL CHECK-IN ----------
@app.route('/api/admin/manual-check-in', methods=['POST'])
def admin_manual_check_in():
    """
    Admin can manually check-in a student immediately (no start/end time provided).
    - Requires: email OR roll_no, seat_id, zone
    - Creates a booking with status='checked_in', start_time = now, end_time = now + MIN_DURATION_MINUTES
    """
    if 'admin_id' not in session:
        return jsonify({'message': 'Admin login required'}), 401

    data = request.get_json() or {}
    email = data.get('email')
    roll_no = data.get('roll_no')
    seat_id = data.get('seat_id')
    zone = data.get('zone')
    booking_date = data.get('booking_date') or datetime.now().strftime("%Y-%m-%d")

    if not all([seat_id, zone]) or not (email or roll_no):
        return jsonify({'message': 'Missing required fields.'}), 400

    # Clean up expired reservations
    cancel_expired_reservations()
    auto_checkout_expired_bookings()

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Find the student
    if email:
        cur.execute("SELECT id, full_name FROM students WHERE email=%s", [email])
    else:
        cur.execute("SELECT id, full_name FROM students WHERE roll_number=%s", [roll_no])
    student = cur.fetchone()

    if not student:
        cur.close()
        return jsonify({'message': 'Student not found.'}), 404

    now = datetime.now()
    start_time_str = now.strftime("%H:%M:%S")
    end_dt = now + timedelta(minutes=MIN_DURATION_MINUTES)
    end_time_str = end_dt.strftime("%H:%M:%S")

    # Check seat availability for the interval
    cur.execute("""
        SELECT id FROM bookings
        WHERE seat_id=%s AND booking_date=%s
          AND status IN ('reserved','checked_in')
          AND (TIMESTAMP(booking_date, start_time) < %s)
          AND (%s < TIMESTAMP(booking_date, end_time))
    """, (seat_id, booking_date, end_time_str, start_time_str))
    conflict = cur.fetchone()

    if conflict:
        cur.close()
        return jsonify({'message': 'Seat is already occupied during that time.'}), 409

    cur.execute("""
        INSERT INTO bookings (user_id, seat_id, booking_date, start_time, end_time, zone, status, checked_in_at)
        VALUES (%s, %s, %s, %s, %s, %s, 'checked_in', NOW())
    """, (student['id'], seat_id, booking_date, start_time_str, end_time_str, zone))
    mysql.connection.commit()

    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE seats 
        SET is_booked = 1, booked_by = %s, booked_at = NOW()
        WHERE seat_number = %s
    """, (student['id'], seat_id))
    mysql.connection.commit()
    cur.close()

    return jsonify({
        'message': f"Manual check-in successful for {student['full_name']} (Seat {seat_id}).",
        'start_time': start_time_str,
        'end_time': end_time_str
    }), 200

# ---------- ADMIN - FIND A FREE SEAT ----------
@app.route('/api/admin/free-seat')
def admin_find_free_seat():
    """
    Returns one free seat in the given zone by checking the bookings table.
    Works without a 'seats' table. Uses static seat naming (A_, B_, C_, D_).
    """
    if 'admin_id' not in session:
        return jsonify({'error': 'Admin login required'}), 401

    zone = request.args.get('zone')
    if not zone:
        return jsonify({'error': 'Zone required'}), 400

    zone = zone.strip().lower()
    zone_map = {
        'zone 1': 'A',
        'zone1': 'A',
        'zone 2': 'B',
        'zone2': 'B',
        'zone 3': 'C',
        'zone3': 'C',
        'zone 4': 'D',
        'zone4': 'D'
    }

    if zone not in zone_map:
        return jsonify({'error': f'Invalid zone: {zone}'}), 400

    prefix = zone_map[zone]

    # Define available seats per zone
    seat_list = [f"{prefix}_{i}" for i in range(1, 21)]

    # Check which seats are already booked today
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT DISTINCT seat_id
        FROM bookings
        WHERE zone = %s AND booking_date = CURDATE()
          AND status IN ('reserved','checked_in')
    """, [zone.title()])
    booked = [r['seat_id'] for r in cur.fetchall()]
    cur.close()

    free_seats = [s for s in seat_list if s not in booked]

    if not free_seats:
        return jsonify({'message': f'No free seats available in {zone.title()} right now'}), 200

    return jsonify({'free_seat': free_seats[0]}), 200

@app.route('/api/admin/list-seats')
def admin_list_seats():
    if 'admin_id' not in session:
        return jsonify({'error':'Admin login required'}), 401
    zone = request.args.get('zone') or ''
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT seat_number, zone, is_booked, booked_by, booked_at FROM seats WHERE zone LIKE %s ORDER BY seat_number ASC LIMIT 500", (f"%{zone}%",))
    rows = cur.fetchall()
    cur.close()
    return jsonify({'rows': rows})

@app.route('/api/admin/checkout', methods=['POST'])
def admin_checkout():
    """Allows admin to manually check out a student and free their seat."""
    if 'admin_id' not in session:
        return jsonify({'message': 'Admin login required'}), 401

    data = request.get_json() or {}
    booking_id = data.get('booking_id')
    if not booking_id:
        return jsonify({'message': 'booking_id required'}), 400

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT id, seat_id, status FROM bookings WHERE id = %s", [booking_id])
    booking = cur.fetchone()

    if not booking:
        cur.close()
        return jsonify({'message': 'Booking not found.'}), 404

    if booking['status'] != 'checked_in':
        cur.close()
        return jsonify({'message': f"Booking not active (status: {booking['status']})."}), 400

    # Update booking to checked_out
    cur.execute("""
        UPDATE bookings
        SET status = 'checked_out', end_time = NOW()
        WHERE id = %s
    """, [booking_id])

    cur.execute("""
        UPDATE seats
        SET is_booked = 0, booked_by = NULL, booked_at = NULL
        WHERE seat_number = %s
    """, [booking['seat_id']])

    mysql.connection.commit()
    cur.close()

    return jsonify({'message': f'Student successfully checked out from seat {booking["seat_id"]}.'}), 200

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

@app.route('/upload-admin-photo', methods=['POST'])
def upload_admin_photo():
    if 'admin_id' not in session:
        flash("Access denied.")
        return redirect(url_for('login'))

    file = request.files.get('photo')
    if not file or file.filename == '':
        flash('No file selected.')
        return redirect(url_for('admin_profile'))

    filename = f"admin_{session['admin_id']}_{file.filename}"
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)

    cur = mysql.connection.cursor()
    cur.execute("UPDATE admins SET photo=%s WHERE id=%s", (filename, session['admin_id']))
    mysql.connection.commit()
    cur.close()

    flash("Profile photo updated successfully.")
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

# ---------- ADMIN - MANAGE BOOKS ----------

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
    if book_id: 
        cur.execute("""
            UPDATE books 
            SET title=%s, author=%s, isbn=%s, category=%s, total_copies=%s, available_copies=%s
            WHERE id=%s
        """, (title, author, isbn, category, total_copies, available_copies, book_id))
    else:  
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

# ---------- ADD ANNOUNCEMENT ----------
@app.route('/api/add-announcement', methods=['POST'])
def add_announcement():
    if 'admin_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized access'}), 403

    try:
        data = request.get_json(force=True, silent=True) or {}
        title = data.get('title')
        message = data.get('message')
        admin_id = session['admin_id'] 

        if not title or not message:
            return jsonify({'status': 'error', 'message': 'Please fill in all fields.'}), 400

        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO announcements (title, message, created_by) VALUES (%s, %s, %s)",
            (title, message, admin_id)
        )
        mysql.connection.commit()
        cur.close()

        return jsonify({'status': 'success', 'message': 'Announcement added successfully!'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

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

@app.route('/announcements')
def announcements():
    if 'admin_id' not in session:
        flash('Access denied.')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT a.id, a.title, a.message, a.created_at, ad.full_name AS created_by
        FROM announcements a
        JOIN admins ad ON a.created_by = ad.id
        ORDER BY a.created_at DESC
    """)
    announcements = cur.fetchall()
    cur.close()

    return render_template('announcements.html', announcements=announcements)

# ---------- ADMIN - ANNOUNCEMENTS ----------
@app.route('/api/admin/announcements')
def api_admin_announcements():
    if 'admin_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT title, message AS content, created_at FROM announcements ORDER BY created_at DESC")
    announcements = cur.fetchall()
    cur.close()

    for a in announcements:
        if isinstance(a['created_at'], datetime):
            a['created_at'] = a['created_at'].strftime("%Y-%m-%d")

    return jsonify({'announcements': announcements})

import threading, time

def background_auto_checkout():
    while True:
        with app.app_context():
            auto_checkout_expired_bookings()
        time.sleep(300) 

threading.Thread(target=background_auto_checkout, daemon=True).start()

# ---- Automatic Booking Cancellation Scheduler ----
scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_cancels, 'interval', seconds=60) 
scheduler.start()

# ----------  MAIN ENTRY ----------
if __name__ == '__main__':
    app.run(debug=True)
