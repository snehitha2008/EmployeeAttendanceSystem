import sqlite3

def get_connection():
    return sqlite3.connect("attendance.db")

def create_tables():
    db = get_connection()
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            department TEXT,
            email TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            attendance_date TEXT,
            status TEXT
        )
    """)

    db.commit()
    db.close()

create_tables()

print("Database created successfully!")