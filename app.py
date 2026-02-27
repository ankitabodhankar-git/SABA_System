from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# ---------------- DATABASE ----------------

def get_connection():
    return sqlite3.connect("saba.db")

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Users table (for login)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            password TEXT,
            role TEXT
        )
    """)

    # Students table (for performance)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            department TEXT,
            attendance INTEGER,
            marks INTEGER
        )
    """)

    # Insert one teacher user if not exists
    cursor.execute("SELECT * FROM users WHERE email=?", ("teacher@asmedu.org",))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (email,password,role) VALUES (?,?,?)",
                       ("teacher1@asmedu.org","1234","teacher"))

    conn.commit()
    conn.close()

# ---------------- LOGIN ----------------

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # College email validation
        if not email.endswith("@asmedu.org"):
            return render_template("login.html", error="Use college email only")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE email=? AND password=?",
                       (email,password))
        user = cursor.fetchone()
        conn.close()

        if user:
            role = user[0]
            return redirect(f"/{role}")
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


# ---------------- TEACHER DASHBOARD ----------------

@app.route("/teacher")
def teacher():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    conn.close()

    total_students = len(students)

    if total_students > 0:
        avg_marks = sum(s[5] for s in students) / total_students
    else:
        avg_marks = 0

    at_risk = 0
    top_marks = 0

    for s in students:
        if s[4] < 60 or s[5] < 40:
            at_risk += 1
        if s[5] > top_marks:
            top_marks = s[5]

    return render_template(
        "teacher_dashboard.html",
        students=students,
        total_students=total_students,
        avg_marks=round(avg_marks,2),
        at_risk=at_risk,
        top_marks=top_marks
    )

# ---------------- ADD PERFORMANCE ----------------

@app.route("/add_performance", methods=["GET","POST"])
def add_performance():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        dept = request.form["department"]
        attendance = request.form["attendance"]
        marks = request.form["marks"]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO students(name,email,department,attendance,marks)
            VALUES(?,?,?,?,?)
        """,(name,email,dept,attendance,marks))

        conn.commit()
        conn.close()

        return redirect("/teacher")

    return render_template("add_performance.html")


if __name__ == "__main__":
    create_tables()
    app.run(debug=True)