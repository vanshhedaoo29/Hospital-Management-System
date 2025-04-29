from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# 📌 Step 4: Setup SQLite database path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'  # This creates hospital.db file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # (Just to silence a warning)

# 📦 Step 5: Initialize database
db = SQLAlchemy(app)

@app.route("/")
def hello_world():
    return render_template('index.html')

@app.route("/appointments")
def appointments():
    return render_template('appointment.html')

@app.route("/doctors")
def doctors():
    return render_template('doctor.html')

@app.route("/aboutus")
def about_us():
    return render_template('aboutus.html')

@app.route("/login")
def login():
    return render_template('patient.html')

@app.route("/signup")
def signup():
    return render_template('patient-register.html')

@app.route("/admin-login")
def admin_login():
    return render_template('admin.html')

@app.route("/admin-signup")
def admin_signup():
    return render_template('admin-register.html')

if __name__ == "__main__":
    app.run(debug=True, port=6969)