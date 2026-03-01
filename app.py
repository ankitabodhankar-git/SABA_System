from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secretkey"

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
        role TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        department TEXT,
        attendance INTEGER DEFAULT 0,
        marks INTEGER DEFAULT 0
    )
    """)

    # Default Admin
    cursor.execute("SELECT * FROM users WHERE email='admin@asmedu.org'")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO users (name,email,password,role)
        VALUES (?,?,?,?)
        """, ("Admin","admin@asmedu.org","admin123","admin"))

    conn.commit()
    conn.close()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("saba.db")
        cursor = conn.cursor()

        cursor.execute("""
        SELECT id, role FROM users
        WHERE email=? AND password=?
        """, (email,password))

        user = cursor.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["role"] = user[1]

            if user[1] == "admin":
                return redirect("/admin")

        return render_template("login.html", error="Invalid Credentials")

    return render_template("login.html")

# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect("/")

    conn = sqlite3.connect("saba.db")
    cursor = conn.cursor()

    # All students with performance
    cursor.execute("""
    SELECT users.name, users.email, students.department,
           students.attendance, students.marks
    FROM students
    JOIN users ON students.user_id = users.id
    """)
    students = cursor.fetchall()

    # Department count
    cursor.execute("""
    SELECT department, COUNT(*)
    FROM students
    GROUP BY department
    """)
    dept_data = cursor.fetchall()

    conn.close()

    return render_template("admin_dashboard.html",
                           students=students,
                           dept_data=dept_data)

# ---------------- ADD STUDENT ----------------
@app.route("/add_student", methods=["GET","POST"])
def add_student():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        department = request.form["department"]

        conn = sqlite3.connect("saba.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO users (name,email,password,role)
        VALUES (?,?,?,?)
        """, (name,email,"123","student"))

        user_id = cursor.lastrowid

        cursor.execute("""
        INSERT INTO students (user_id,department,attendance,marks)
        VALUES (?,?,?,?)
        """, (user_id,department,0,0))

        conn.commit()
        conn.close()

        return redirect("/admin")

    return render_template("add_student.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    create_tables()
    app.run(debug=True)