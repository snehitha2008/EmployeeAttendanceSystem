
from flask import Flask, render_template, request, redirect
from database import get_connection
import csv
import io

app = Flask(__name__)


# 1. Dashboard
@app.route("/")
def home():

    search = request.args.get("search", "")
    department = request.args.get("department", "")

    db = get_connection()
    cursor = db.cursor()

    # Dashboard counts
    cursor.execute("SELECT COUNT(*) FROM employees")
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM attendance
        WHERE attendance_date = DATE('now')
        AND status = 'Present'
    """)
    present = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM attendance
        WHERE attendance_date = DATE('now')
        AND status = 'Absent'
    """)
    absent = cursor.fetchone()[0]

    percentage = round((present / total) * 100, 2) if total else 0

    # Employee search and department filter
    query = "SELECT * FROM employees WHERE name LIKE ?"
    values = ["%" + search + "%"]

    if department:
        query += " AND department = ?"
        values.append(department)

    cursor.execute(query, values)
    employees = cursor.fetchall()

    # Department list
    cursor.execute("SELECT DISTINCT department FROM employees")
    departments = cursor.fetchall()

    # Attendance records
    cursor.execute("""
        SELECT employees.name,
               attendance.attendance_date,
               attendance.status
        FROM attendance
        JOIN employees
        ON employees.id = attendance.employee_id
        ORDER BY attendance.id DESC
    """)
    records = cursor.fetchall()

    db.close()

    return render_template(
        "index.html",
        total=total,
        present=present,
        absent=absent,
        percentage=percentage,
        employees=employees,
        records=records,
        departments=departments,
        search=search,
        selected_department=department
    )


# 2. Add Employee
@app.route("/add_employee", methods=["POST"])
def add_employee():

    name = request.form["name"].strip()
    department = request.form["department"].strip()
    email = request.form["email"].strip()

    if not name or not department or not email:
        return "Please fill in all details."

    db = get_connection()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO employees (name, department, email)
        VALUES (?, ?, ?)
    """, (name, department, email))

    db.commit()
    db.close()

    return redirect("/")


# 3. Mark Attendance
@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():

    employee_id = request.form["employee_id"]
    status = request.form["status"]

    if status not in ["Present", "Absent"]:
        return "Invalid attendance status."

    db = get_connection()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO attendance
        (employee_id, attendance_date, status)
        VALUES (?, DATE('now'), ?)
    """, (employee_id, status))

    db.commit()
    db.close()

    return redirect("/")


# 4. Bulk Upload Employees using CSV
@app.route("/upload_employees", methods=["POST"])
def upload_employees():

    file = request.files.get("file")

    if not file or file.filename == "":
        return "Please select a CSV file."

    if not file.filename.lower().endswith(".csv"):
        return "Please upload a CSV file."

    db = None

    try:
        content = file.stream.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))

        required_columns = {"Name", "Department", "Email"}

        if not reader.fieldnames or not required_columns.issubset(
            set(reader.fieldnames)
        ):
            return "CSV must contain Name, Department and Email columns."

        db = get_connection()
        cursor = db.cursor()

        count = 0

        for row in reader:

            name = (row.get("Name") or "").strip()
            department = (row.get("Department") or "").strip()
            email = (row.get("Email") or "").strip()

            if not name or not department or not email:
                continue

            cursor.execute("""
                INSERT INTO employees (name, department, email)
                VALUES (?, ?, ?)
            """, (name, department, email))

            count += 1

        db.commit()
        db.close()

        # Return to the complete dashboard
        return redirect("/")

    except Exception as e:
        if db:
            db.rollback()
            db.close()

        return "Upload failed: " + str(e)


# 5. Run Website
if __name__ == "__main__":
    app.run(debug=True)
