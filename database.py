import sqlite3

DATABASE = "gold_loan.db"


# ---------------- DATABASE CONNECTION ---------------- #

def get_connection():

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    return conn


# ---------------- CREATE TABLES ---------------- #

def create_tables():

    conn = get_connection()
    cursor = conn.cursor()

    # ================= CUSTOMERS TABLE ================= #

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL,

    mobile TEXT NOT NULL,

    email TEXT,

    dob TEXT,

    gender TEXT,

    occupation TEXT,
    
    address TEXT ,

    aadhaar TEXT ,

    nominee_name TEXT,

    nominee_relation TEXT,

    nominee_mobile TEXT,

    photo TEXT,

    remarks TEXT

)
    """)

    # ================= LOANS TABLE ================= #

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS loans(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        loan_number TEXT UNIQUE NOT NULL,

        customer_id INTEGER NOT NULL,

        ornament_type TEXT NOT NULL,

        quantity INTEGER NOT NULL,

        description TEXT,

        gross_weight REAL NOT NULL,

        stone_weight REAL NOT NULL DEFAULT 0,

        net_weight REAL NOT NULL,

        purity TEXT NOT NULL,

        gold_rate REAL NOT NULL,

        gold_value REAL NOT NULL,

        eligible_amount REAL NOT NULL,

        loan_amount REAL NOT NULL,

        outstanding_amount REAL NOT NULL,

        interest_rate REAL NOT NULL,

        loan_date TEXT NOT NULL,

        due_date TEXT NOT NULL,

        status TEXT NOT NULL DEFAULT 'Active',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(customer_id)
        REFERENCES customers(id)

    )
    """)

   

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        loan_id INTEGER NOT NULL,

        payment_date TEXT NOT NULL,

        interest_paid REAL NOT NULL,

        principal_paid REAL NOT NULL,

        total_paid REAL NOT NULL,

        balance REAL NOT NULL,

        remarks TEXT,

        FOREIGN KEY(loan_id)
        REFERENCES loans(id)

    )
    """)
         # ================= USERS TABLE =================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT UNIQUE NOT NULL,

        password TEXT NOT NULL

    )
    """)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'employee'")
    except Exception:
        pass
    cursor.execute("""
    INSERT OR IGNORE INTO users(username, password, role)
    VALUES('Sarang', '1234', 'admin')
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO users(username, password, role)
    VALUES('Antony', '5678', 'employee')
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO users(username, password)
    VALUES('admin', '1234')
    """)
    conn.commit()
    conn.close()
# ---------------- LOAN NUMBER GENERATOR ---------------- #

def generate_loan_number():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COUNT(*)
    FROM loans
    """)

    count = cursor.fetchone()[0] + 1

    conn.close()

    return f"GL{count:06d}"