from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "saba_secret_key"

# ---------------- DATABASE ----------------
def create_tables():
    conn = sqlite3.connect("saba.db")
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT,
        department TEXT
    )
    """)

    # SEMESTER PERFORMANCE TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS semester_performance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        semester INTEGER,
        attendance INTEGER,
        marks INTEGER,
        behaviour INTEGER,
        overall_score REAL,
        risk_status TEXT
    )
    """)

    # DEFAULT ADMIN
    cursor.execute("SELECT * FROM users WHERE email='admin@asmedu.org'")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO users (name,email,password,role,department)
        VALUES (?,?,?,?,?)
        """, ("Admin","admin@asmedu.org","admin123","admin","ADMIN"))

    conn.commit()
    conn.close()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if not email.endswith("@asmedu.org"):
            return render_template("login.html", error="Only college email allowed")

        conn = sqlite3.connect("saba.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id,role FROM users WHERE email=? AND password=?",
                       (email,password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["role"] = user[1]

            if user[1] == "admin":
                return redirect("/admin")
            elif user[1] == "teacher":
                return redirect("/teacher")
            elif user[1] == "student":
                return redirect("/student")

        return render_template("login.html", error="Invalid Credentials")

    return render_template("login.html")

# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect("/")

    conn = sqlite3.connect("saba.db")
    cursor = conn.cursor()

    # All students
    cursor.execute("SELECT id,name,email,department FROM users WHERE role='student'")
    students = cursor.fetchall()

    # Department wise count
    cursor.execute("""
    SELECT department, COUNT(*)
    FROM users
    WHERE role='student'
    GROUP BY department
    """)
    dept_count = cursor.fetchall()

    conn.close()

    return render_template("admin_dashboard.html",
                           students=students,
                           dept_count=dept_count)

# ---------------- ADD STUDENT ----------------
@app.route("/add_student", methods=["GET","POST"])
def add_student():
    if session.get("role") != "admin":
        return redirect("/")

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        department = request.form["department"]

        if not email.endswith("@asmedu.org"):
            return "Only college email allowed"

        conn = sqlite3.connect("saba.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO users (name,email,password,role,department)
        VALUES (?,?,?,?,?)
        """, (name,email,password,"student",department))

        conn.commit()
        conn.close()

        return redirect("/admin")

    return render_template("add_student.html")

# ---------------- TEACHER DASHBOARD ----------------
@app.route("/teacher")
def teacher_dashboard():
    if session.get("role") != "teacher":
        return redirect("/")
    return render_template("teacher_dashboard.html")

# ---------------- ADD PERFORMANCE ----------------
@app.route("/add_performance", methods=["GET","POST"])
def add_performance():
    if session.get("role") != "teacher":
        return redirect("/")

    if request.method == "POST":
        student_id = request.form["student_id"]
        semester = int(request.form["semester"])
        attendance = int(request.form["attendance"])
        marks = int(request.form["marks"])
        behaviour = int(request.form["behaviour"])

        overall = (attendance * 0.3) + (marks * 0.4) + (behaviour * 0.3)

        if overall >= 75:
            risk = "Good"
        elif overall >= 50:
            risk = "Average"
        else:
            risk = "At Risk"

        conn = sqlite3.connect("saba.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO semester_performance
        (student_id,semester,attendance,marks,behaviour,overall_score,risk_status)
        VALUES (?,?,?,?,?,?,?)
        """, (student_id,semester,attendance,marks,behaviour,overall,risk))

        conn.commit()
        conn.close()

        return redirect("/teacher")

    return render_template("add_performance.html")

# ---------------- STUDENT DASHBOARD ----------------
@app.route("/student")
def student_dashboard():
    if session.get("role") != "student":
        return redirect("/")

    conn = sqlite3.connect("saba.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT semester,attendance,marks,behaviour,overall_score,risk_status
    FROM semester_performance
    WHERE student_id=?
    """, (session["user_id"],))

    performance = cursor.fetchall()
    conn.close()

    return render_template("student_dashboard.html",
                           performance=performance)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    create_tables()
    app.run(debug=True)