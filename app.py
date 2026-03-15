from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "saba_secret_key"

# ---------------- DATABASE ----------------
def create_tables():
    conn = sqlite3.connect("saba.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT,
    department TEXT,
    year TEXT
)
    """)

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

    cursor.execute("SELECT * FROM users WHERE email='admin@asmedu.org'")
    if not cursor.fetchone():
        cursor.execute("""
INSERT INTO users (name,email,password,role,department,year)
VALUES (?,?,?,?,?,?)
""", ("Admin","admin@asmedu.org","admin123","admin","ADMIN","Admin"))

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

    cursor.execute("SELECT id,name,email,department FROM users WHERE role='student'")
    students = cursor.fetchall()

    cursor.execute("""
    SELECT department, COUNT(*)
    FROM users
    WHERE role='student'
    GROUP BY department
    """)
    dept_count = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM users WHERE role='teacher'")
    teacher_count = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "admin_dashboard.html",
        students=students,
        dept_count=dept_count,
        teacher_count=teacher_count
    )


# ---------------- ADD STUDENT ----------------
@app.route("/add_student", methods=["GET","POST"])
def add_student():

    if session.get("role") != "admin":
        return redirect("/")

    if request.method == "POST":

        name = request.form["name"]
        # auto email generated
        username = name.lower().replace(" ", ".")
        email = username + "@asmedu.org"
        password = request.form["password"]
        department = request.form["department"]
        year = request.form["year"]

        if not email.endswith("@asmedu.org"):
            return "Only college email allowed"

        conn = sqlite3.connect("saba.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO users (name,email,password,role,department,year)
        VALUES (?,?,?,?,?,?)
        """,(name,email,password,"student",department,year))

        conn.commit()
        conn.close()

        return render_template("add_student.html", generated_email=email)

    return render_template("add_student.html")


# ---------------- TEACHER DASHBOARD ----------------
@app.route("/teacher")
def teacher_dashboard():
    if session.get("role") != "teacher":
        return redirect("/")

    conn = sqlite3.connect("saba.db")
    cursor = conn.cursor()

    # Get teacher's department
    cursor.execute("SELECT department FROM users WHERE id=?", (session["user_id"],))
    teacher_dept = cursor.fetchone()[0]

    # Students only from this department
    cursor.execute("SELECT id,name FROM users WHERE role='student' AND department=?", (teacher_dept,))
    students = cursor.fetchall()
    total_students = len(students)

    # Performance counts only for this department
    cursor.execute("""
        SELECT risk_status, COUNT(*)
        FROM semester_performance sp
        JOIN users u ON sp.student_id = u.id
        WHERE u.department=?
        GROUP BY risk_status
    """, (teacher_dept,))
    stats = dict(cursor.fetchall())

    good = stats.get("Good", 0)
    avg = stats.get("Average", 0)
    risk = stats.get("At Risk", 0)

    conn.close()

    return render_template(
        "teacher_dashboard.html",
        total_students=total_students,
        good=good,
        avg=avg,
        risk=risk,
        students=students,
        teacher_dept=teacher_dept
    )



# ---------------- STUDENT LIST ----------------
@app.route("/student_list")
def student_list():

    if session.get("role") != "admin":
        return redirect("/")

    conn = sqlite3.connect("saba.db")
    cursor = conn.cursor()

    cursor.execute("SELECT name,email,department,year FROM users WHERE role='student'")
    students = cursor.fetchall()

    conn.close()

    return render_template("student_list.html", students=students)

# ---------------- TEACHER LIST ----------------
@app.route("/teacher_list")
def teacher_list():

    if session.get("role") != "admin":
        return redirect("/")

    conn = sqlite3.connect("saba.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT name, email, department
    FROM users
    WHERE role='teacher'
    """)

    teachers = cursor.fetchall()

    conn.close()

    return render_template("teacher_list.html", teachers=teachers)


# ---------------- ADD TEACHER ----------------
@app.route("/add_teacher", methods=["GET","POST"])
def add_teacher():

    if session.get("role") != "admin":
        return redirect("/")

    if request.method == "POST":

        name = request.form["name"]
        # auto geneted email
        username = name.lower().replace(" " ,"")
        email = username + "@asmedu.org"
        password = request.form["password"]
        department = request.form["department"]

        if not email.endswith("@asmedu.org"):
            return "Only college email allowed"

        conn = sqlite3.connect("saba.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO users (name,email,password,role,department,year)
        VALUES (?,?,?,?,?,?)
        """,(name,email,password,"teacher",department,"NA"))

        conn.commit()
        conn.close()

        return redirect("/admin")

    return render_template("add_teacher.html")


# ---------------- ADD PERFORMANCE ----------------
@app.route("/add_performance", methods=["GET","POST"])
def add_performance():

    if session.get("role") != "teacher":
        return redirect("/")

    student_id = request.args.get("student_id")

    if request.method == "POST":

        student_id = request.form.get("student_id")
        semester = request.form["semester"]
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
        """,(student_id,semester,attendance,marks,behaviour,overall,risk))

        conn.commit()
        conn.close()

        return redirect("/teacher")

    return render_template("add_performance.html", student_id=student_id)


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

# ---------------- MY STUDENTS LIST----------------
@app.route("/students")
def students_page():
    if session.get("role") != "teacher":
        return redirect("/")

    conn = sqlite3.connect("saba.db")
    cursor = conn.cursor()

    # Get teacher's department
    cursor.execute("SELECT department FROM users WHERE id=?", (session["user_id"],))
    teacher_dept = cursor.fetchone()[0]

    # Fetch only students from this department
    cursor.execute("SELECT id, name FROM users WHERE role='student' AND department=?", (teacher_dept,))
    students = cursor.fetchall()

    conn.close()

    return render_template("students.html", students=students, teacher_dept=teacher_dept)

# ---------------- CHANGE PWD ----------------
@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if not session.get("user_id"):
        return redirect("/")

    if request.method == "POST":
        old_pwd = request.form["old_password"]
        new_pwd = request.form["new_password"]

        conn = sqlite3.connect("saba.db")
        cursor = conn.cursor()

        # Verify old password
        cursor.execute("SELECT password FROM users WHERE id=?", (session["user_id"],))
        current_pwd = cursor.fetchone()[0]

        if current_pwd != old_pwd:
            conn.close()
            return render_template("change_password.html", error="Old password incorrect")

        # Update new password
        cursor.execute("UPDATE users SET password=? WHERE id=?", (new_pwd, session["user_id"]))
        conn.commit()
        conn.close()

        # Redirect based on role
        if session.get("role") == "teacher":
            return redirect("/teacher")
        elif session.get("role") == "student":
            return redirect("/student_dashboard")
        else:
            return redirect("/")

    return render_template("change_password.html")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    create_tables()
    app.run(debug=True)