from flask import Flask, render_template, request, redirect, url_for, session, flash , abort
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.text import MIMEText
import razorpay
import hmac
import hashlib

app = Flask(__name__)
app.secret_key = 'jevlakay'

WEBHOOK_SECRET = "jevlakay"  # Same as set in Razorpay dashboard

# Razorpay credentials
razorpay_client = razorpay.Client(auth=("rzp_test_ssENo9FiYrNaQF", "Ux56gbRZb11oRdKoiASOQW0u"))

DB_NAME = 'hospital.db'

# Create all necessary tables
# def init_db():
#     conn = sqlite3.connect(DB_NAME)
#     cursor = conn.cursor()
    
#     # Users table
#     cursor.execute('''CREATE TABLE IF NOT EXISTS users (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         name TEXT NOT NULL,
#         email TEXT UNIQUE NOT NULL,
#         password TEXT NOT NULL
#     )''')

#     # Appointments table
#     # cursor.execute('''CREATE TABLE IF NOT EXISTS appointments (
#     #     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     #     firstname TEXT NOT NULL,
#     #     lastname TEXT NOT NULL,
#     #     email TEXT NOT NULL,
#     #     number TEXT NOT NULL,
#     #     doctor TEXT NOT NULL,
#     #     date TEXT NOT NULL,
#     #     time TEXT NOT NULL,
#     #     appointment_type TEXT NOT NULL,
#     #     notes TEXT
#     # )''')
    
#     # Admin table
#     cursor.execute('''CREATE TABLE IF NOT EXISTS admins (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         fullname TEXT NOT NULL,
#         email TEXT UNIQUE NOT NULL,
#         password TEXT NOT NULL
#     )''')
    
#     # Insert default admin if none exists
#     cursor.execute("SELECT * FROM admins")
#     if cursor.fetchone() is None:
#         cursor.execute("INSERT INTO admins (email, password) VALUES (?, ?)", (
#             "admin@example.com", generate_password_hash("admin123")
#         ))
        
#     # Create tables if not exist
#     cursor.execute('''CREATE TABLE IF NOT EXISTS users (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         name TEXT NOT NULL,
#         email TEXT UNIQUE NOT NULL,
#         password TEXT NOT NULL
#     )''')

#     cursor.execute('''CREATE TABLE IF NOT EXISTS appointments (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         firstname TEXT NOT NULL,
#         lastname TEXT NOT NULL,
#         email TEXT NOT NULL,
#         number TEXT NOT NULL,
#         doctor TEXT NOT NULL,
#         date TEXT NOT NULL,
#         time TEXT NOT NULL,
#         appointment_type TEXT NOT NULL,
#         notes TEXT
#     )''')

#     cursor.execute('''CREATE TABLE IF NOT EXISTS admins (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         fullname TEXT NOT NULL,
#         email TEXT UNIQUE NOT NULL,
#         password TEXT NOT NULL
#     )''')

#     # Check if 'status' column already exists
#     cursor.execute("PRAGMA table_info(appointments)")
#     columns = [col[1] for col in cursor.fetchall()]
#     if 'status' not in columns:
#         cursor.execute("ALTER TABLE appointments ADD COLUMN status TEXT DEFAULT 'Pending'")
        
#     # Add 'fullname' column to admins if not exists
#     cursor.execute("PRAGMA table_info(admins)")
#     admin_columns = [col[1] for col in cursor.fetchall()]
#     if 'fullname' not in admin_columns:
#         cursor.execute("ALTER TABLE admins ADD COLUMN fullname TEXT")    

#     conn.commit()
#     conn.close()





def init_db():
    with sqlite3.connect(DB_NAME, timeout=10) as conn:
        cursor = conn.cursor()

        # Create tables
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            number TEXT NOT NULL,
            password TEXT NOT NULL
        )''')
        
        cursor.execute("DROP TABLE IF EXISTS messages")

        cursor.execute('''
            CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            number TEXT NOT NULL,
            message TEXT
        )''')


        cursor.execute('''CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firstname TEXT NOT NULL,
            lastname TEXT NOT NULL,
            email TEXT NOT NULL,
            number TEXT NOT NULL,
            doctor TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            appointment_type TEXT NOT NULL,
            notes TEXT,
            status TEXT DEFAULT 'Pending'
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )''')

        # Check if default admin exists
        cursor.execute("SELECT * FROM admins WHERE email=?", ("admin@example.com",))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO admins (fullname, email, password) VALUES (?, ?, ?)", (
                "Default Admin", "admin@example.com", generate_password_hash("admin123")
            ))

        conn.commit()


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/home")
def main():
    return redirect(url_for("home"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT name, password FROM users WHERE email=?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session["user"] = user[0]
            flash("✅ Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("❌ Invalid credentials", "error")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
            conn.commit()
            conn.close()
            flash("👤 Account created!", "account")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already registered!")
            return redirect(url_for("signup"))

    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("🔐 Logged out successfully.", "logout")
    return redirect(url_for("login"))

# Flask Route for Appointments
@app.route("/appointments", methods=["GET", "POST"])
def appointments():
    if request.method == "POST":
        data = {
            "firstname": request.form["firstname"],
            "lastname": request.form["lastname"],
            "email": request.form["email"],
            "number": request.form["number"],
            "doctor": request.form["doctor"],
            "date": request.form["date"],
            "time": request.form["time"],
            "appointment_type": request.form["type"],
            "notes": request.form.get("notes", ""),
            "status": "Pending"
        }

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO appointments 
            (firstname, lastname, email, number, doctor, date, time, appointment_type, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (data["firstname"], data["lastname"], data["email"], data["number"], data["doctor"],
             data["date"], data["time"], data["appointment_type"], data["notes"], data["status"])
        )

        conn.commit()
        conn.close()
        flash("📅 Appointment request sent!", "appointment")
        return redirect(url_for("home"))

    return render_template("appointment.html")


@app.route("/doctors")
def doctors():
    return render_template("doctor.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        data = {
            "name": request.form["name"],
            "email": request.form["email"],
            "number": request.form["number"],
            "message": request.form.get("message", "")
        }

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Ensure the 'messages' table exists
        cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            number TEXT NOT NULL,
            message TEXT
        )''')

        # Insert into the messages table
        cursor.execute('''
            INSERT INTO messages 
            (name, email, number, message)
            VALUES (?, ?, ?, ?)''',
            (data["name"], data["email"], data["number"], data["message"])
        )

        conn.commit()
        conn.close()
        flash("📤 Message successfully sent!", "message")
        return redirect(url_for("contact"))

    return render_template("contact.html")

@app.route("/dashboard/messages" , methods=["GET", "POST"])
def messages():
    if not session.get("admin_logged_in"):
        flash("⛔ Admin access required", "m-error")
        return redirect(url_for("admin_login"))
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Make sure your table includes 'number' column
    cursor.execute("SELECT * FROM messages ORDER BY id DESC")
    messages = cursor.fetchall()

    conn.close()
    return render_template("messages.html", messages=messages)


@app.route("/dashboard/adddoctor" , methods=["GET", "POST"])
def adddoctor():
    return render_template("adddoctor.html")

@app.route("/aboutus")
def about_us():
    return render_template("aboutus.html")

# Dashboard Route (Login Protected)
@app.route("/dashboard" , methods=["GET", "POST"])
def dashboard():
    if not session.get("admin_logged_in"):
        flash("⚠️ Admin login required", "error")
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appointments ORDER BY date DESC, time ASC")
    appointments = cursor.fetchall()
    conn.close()

    return render_template("dashboard.html", appointments=appointments)

# Admin Login Route
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        print(f"Attempting login with: {email} / {password}")

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM admins WHERE email=?", (email,))
        admin = cursor.fetchone()
        conn.close()
        
        print(f"Fetched admin from DB: {admin}")

        if admin and check_password_hash(admin[0], password):
            session["admin_logged_in"] = True
            flash("✅ Admin login successful!", "in-success")
            return redirect(url_for("dashboard"))
        else:
            flash("❌ Invalid admin credentials", "in-error")
            return redirect(url_for("admin_login"))

    return render_template("admin-login.html")

# Admin Signup Route
@app.route("/admin-signup", methods=["GET", "POST"])
def admin_signup():
    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO admins (fullname, email, password) VALUES (?, ?, ?)",
                           (fullname, email, password))
            conn.commit()
            conn.close()
            flash("✅ Admin account created!", "up-success")
            return redirect(url_for("admin_login"))
        except sqlite3.IntegrityError:
            flash("❌ Admin email already registered!", "up-error")
            return redirect(url_for("admin_signup"))

    return render_template("admin-signup.html")

@app.route("/admin-logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("🔐 Logged out from Admin.", "info")
    return redirect(url_for("admin_login"))


def create_payment_link(amount, patient_email):
    response = razorpay_client.payment_link.create({
        "amount": amount * 100,  # Razorpay accepts amount in paise
        "currency": "INR",
        "accept_partial": False,
        "description": "Orchid Clinic Appointment Fees",
        "customer": {
            "email": patient_email
        },
        "notify": {
            "email": True
        },
        "callback_url": "http://yourdomain.com/payment_status",  # Optional
        "callback_method": "get"
    })
    return response['short_url']

def send_email(to, subject, body):
    sender = "earliestpath01@gmail.com"
    password = "bwob fimg tycj kpik"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, to, msg.as_string())



# @app.route("/update_status/<int:id>", methods=["POST"])
# def update_status(id):
#     new_status = request.form["status"]

#     # Update the status in the database
#     conn = sqlite3.connect(DB_NAME)
#     cursor = conn.cursor()
#     cursor.execute("UPDATE appointments SET status=? WHERE id=?", (new_status, id))

#     # Get the user's email address
#     cursor.execute("SELECT email FROM appointments WHERE id=?", (id,))
#     email = cursor.fetchone()[0]
#     conn.commit()
#     conn.close()

#     # Send email for Approved or Cancelled
#     if new_status == "Cancelled":
#         subject = f"Your Appointment has been {new_status}"
#         body = f"""Dear Patient,

# Your appointment has been {new_status.lower()}.

# Regards,  
# Orchid Clinic"""
#         send_email(email, subject, body)
        
#     if new_status == "Approved":
#     payment_link = create_payment_link(500, email)  # Change 500 to your actual fee
#     subject = "Your Appointment is Approved – Payment Required"
#     body = f"""Dear Patient,

# Your appointment has been approved. Please complete the payment of ₹500 at the link below:

# {payment_link}

# Regards,
# Orchid Clinic
# """
#     send_email(email, subject, body)    

#     flash(f"📧 Appointment status updated to {new_status}", "s-updated")
#     return redirect(url_for("dashboard"))



@app.route("/update_status/<int:id>", methods=["POST"])
def update_status(id):
    new_status = request.form["status"]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Update status
    cursor.execute("UPDATE appointments SET status=? WHERE id=?", (new_status, id))

    # Get email for the appointment
    cursor.execute("SELECT email FROM appointments WHERE id=?", (id,))
    result = cursor.fetchone()
    email = result[0] if result else None
    conn.commit()
    conn.close()

    # If Approved, send payment link
    if new_status == "Approved" and email:
        payment_link = create_payment_link(500, email)  # 500 is the appointment fee
        subject = "Your Appointment is Approved – Payment Link"
        body = f"""Dear Patient,

Your appointment has been approved.

Please pay ₹500 using the secure Razorpay link below to confirm your appointment:

{payment_link}

Thank you,
Orchid Clinic"""
        send_email(email, subject, body)

    # If Cancelled, notify user
    elif new_status == "Cancelled" and email:
        subject = "Your Appointment is Cancelled"
        body = f"""Dear Patient,

Your appointment has been cancelled.

Regards,
Orchid Clinic"""
        send_email(email, subject, body)

    flash(f"📧 Appointment status updated to {new_status}", "s-updated")
    return redirect(url_for("dashboard"))


@app.route("/payment_webhook", methods=["POST"]) 
def payment_webhook():
    payload = request.data
    received_signature = request.headers.get('X-Razorpay-Signature')

    generated_signature = hmac.new(
        bytes(WEBHOOK_SECRET, 'utf-8'),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(received_signature, generated_signature):
        abort(400)

    data = request.get_json()

    if data['event'] == "payment.link.paid":
        payment_id = data['payload']['payment_link']['entity']['id']
        email = data['payload']['payment_link']['entity']['customer']['email']

        # Update DB
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE appointments SET payment_status='Paid' WHERE email=?", (email,))
        conn.commit()
        conn.close()

        print(f"✅ Payment received for {email}, Payment ID: {payment_id}")

    return "", 200


@app.route("/dashboard/payment_logs")
def payment_logs():
    if "admin_logged_in" not in session:
        flash("❌ Please log in as admin", "danger")
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, status, payment_status FROM appointments WHERE payment_status='Paid'")
    paid_appointments = cursor.fetchall()
    conn.close()

    return render_template("payment_logs.html", appointments=paid_appointments)




if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=10000)
    # app.run(debug=True, port=4518)
