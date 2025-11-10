QuietQueue: A Smart Library Seat & Resource Management System

Project Overview :
  QuietQueue is a digital library management and seat-booking system designed to streamline library operations for both students and administrators.

  It allows:
  Students to register, verify via OTP, log in, book study seats, search books, and manage their bookings.
  Admins to manage users, books, and announcements efficiently through a dedicated dashboard.

1. Pre-Requisite Software
  Before running the project, ensure the following software is installed:

  Required Software :
  Python 3.10+
  XAMPP (for MySQL database)
  pip (Python package manager)

  Required Python Libraries :
  Install all dependencies with: pip install -r requirements.txt
  This installs:
  Flask==2.2.5
  Flask-MySQLdb==1.0.1
  itsdangerous==2.1.2
  python-dotenv==1.0.0

2. Database Setup
  Open XAMPP Control Panel → Start Apache and MySQL.
  Open phpMyAdmin → Create a new database: quietqueue
  Import or execute the provided quietqueue.sql file to create all tables (users, seats, bookings, announcements, etc.).

3. User Accounts & Authentication
  Student Accounts :
  Students can register directly via the /register page.
  Registration includes:
  Email OTP verification (via the /verify-otp route)
  Secure hashed password storage

  Admin Accounts :
  Admin accounts are created manually through MySQL.
  Steps to Create an Admin Account :
  Run the generate_hash.py script to hash a plain-text password: python generate_hash.py
  Open phpMyAdmin, select the quietqueue database, and insert a new record in the admins table:
    INSERT INTO admins (username, email, password) 
    VALUES ('Admin', 'admin@example.com', 'PASTE_HASH_HERE');
  Use those credentials to log in via the admin login page (/login).

4. Present Accounts Used
  Student Accounts :            Password
  iit2024254@iiita.ac.in          1234
  iib2024021@iiita.ac.in          123
  iib2024007@iiita.ac.in          123

  Admin Account :
  rithwika.mode@gmail.com         123

5. Running the Project
  Start MySQL and Apache via XAMPP.
  Run the Flask Application : python app.py
  Open in your browser : http://127.0.0.1:5000/

6. How to Use (Step-by-Step)
  For Students :
  Register → Fill credentials and verify your account using the OTP sent via email.
  Login → Enter valid credentials and Dashboard opens.
  Forgot Password → Enter email and verify OTP → Reset password
  Book Seats → Choose zone, date, and time slot. Choose seat and reserved.
  View/Cancel Bookings → From “Your Bookings” page.
  Check-out → Check-out from your reserved seat from Upcoming Booking/Ongoing booking on Dashboard.
  Search Books → Use the book search interface.
  Profile Page → Update profile or logout.

  For Admins :
  Login using the credentials you created in MySQL.
  Dashboard → View current seat usage and bookings, Check-in students.
  Manage Books → Add / delete / edit books.
  Manage Users → View or delete registered students.
  Announcements → Post and manage library notices.
  Profile Page → Edit admin info or logout.

7. Notes
  Ensure that MySQL is running before executing the Flask application.
  If email OTP is not functioning, verify Gmail app password or disable 2FA.
  Works best on Google Chrome or Microsoft Edge.
  Keep the terminal open while the app is running.
  If port 5000 is already in use, modify app.py: app.run(port=5001)