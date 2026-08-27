import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session
from database import get_connection, create_tables, generate_loan_number

app = Flask(__name__)
app.secret_key = "goldloan123"
UPLOAD_FOLDER = "static/uploads/customers"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
create_tables()
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return render_template(
                "login.html",
                error="Please enter username and password"
            )

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            session["user"] = username
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect(url_for("admin"))

            if user["role"] == "employee":
                return redirect(url_for("employee"))

            return redirect(url_for("home"))

        return render_template(
            "login.html",
            error="Invalid Username or Password"
        )

    return render_template("login.html")
@app.route("/")
def home():

    if "user" not in session:
        return redirect(url_for("login"))

    return render_template(
        "home.html",
        total_customers=0,
        total_loans=0,
        active_loans=0,
        outstanding=0,
        username=session.get("user"),
        role=session.get("role")
    )
@app.route("/customers")
def customers():
    conn = get_connection()
    cur = conn.cursor()
    search = request.args.get("search", "").strip()
    if search:
        like = f"%{search}%"
        cur.execute(
            """SELECT * FROM customers
               WHERE name LIKE ? OR mobile LIKE ? OR aadhaar LIKE ?
               ORDER BY id DESC""",
            (like, like, like),
        )
    else:
        cur.execute("SELECT * FROM customers ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return render_template("customers.html", customers=rows, search=search)
@app.route("/customer/<int:id>")
def customer_profile(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM customers WHERE id=?",
        (id,)
    )

    customer = cur.fetchone()

    cur.execute(
        """
        SELECT *
        FROM loans
        WHERE customer_id=?
        ORDER BY id DESC
        """,
        (id,)
    )

    loans = cur.fetchall()

    cur.execute(
        """
        SELECT COALESCE(SUM(outstanding_amount),0)
        FROM loans
        WHERE customer_id=?
        AND status='Active'
        """,
        (id,)
    )

    outstanding = cur.fetchone()[0]

    conn.close()

    return render_template(
        "customer_profile.html",
        customer=customer,
        loans=loans,
        outstanding=outstanding
    )
@app.route("/payment/<int:loan_id>", methods=["GET", "POST"])
def payment(loan_id):

    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":

        interest_paid = float(request.form["interest_paid"])
        principal_paid = float(request.form["principal_paid"])
        remarks = request.form["remarks"]

        # Get current loan
        cur.execute(
            "SELECT * FROM loans WHERE id=?",
            (loan_id,)
        )

        loan = cur.fetchone()

        total_paid = interest_paid + principal_paid

        new_balance = loan["outstanding_amount"] - principal_paid

        if new_balance < 0:
            new_balance = 0

        status = "Closed" if new_balance == 0 else "Active"

        # Save payment
        cur.execute("""
            INSERT INTO payments(
                loan_id,
                payment_date,
                interest_paid,
                principal_paid,
                total_paid,
                balance,
                remarks
            )
            VALUES(
                ?, DATE('now'), ?, ?, ?, ?, ?
            )
        """, (
            loan_id,
            interest_paid,
            principal_paid,
            total_paid,
            new_balance,
            remarks
        ))

        # Update loan
        cur.execute("""
            UPDATE loans
            SET outstanding_amount=?,
                status=?
            WHERE id=?
        """, (
            new_balance,
            status,
            loan_id
        ))

        conn.commit()

        conn.close()

        return redirect(url_for("loans"))

    cur.execute("""
        SELECT
            loans.*,
            customers.name
        FROM loans
        JOIN customers
            ON customers.id = loans.customer_id
        WHERE loans.id=?
    """, (loan_id,))

    loan = cur.fetchone()

    conn.close()

    return render_template(
        "payment.html",
        loan=loan
    )
@app.route("/payment_history/<int:loan_id>")
def payment_history(loan_id):

    conn = get_connection()
    cur = conn.cursor()

    # Loan Details
    cur.execute("""
        SELECT
            loans.loan_number,
            customers.name
        FROM loans
        JOIN customers
            ON customers.id = loans.customer_id
        WHERE loans.id=?
    """, (loan_id,))

    loan = cur.fetchone()

    # Payment History
    cur.execute("""
        SELECT *
        FROM payments
        WHERE loan_id=?
        ORDER BY id DESC
    """, (loan_id,))

    payments = cur.fetchall()

    conn.close()

    return render_template(
        "payment_history.html",
        loan=loan,
        payments=payments
    )
# ================= EDIT CUSTOMER =================
@app.route("/add_customer", methods=["GET", "POST"])

def add_customer():

    if request.method == "POST":

        name = request.form["name"]
        mobile = request.form["mobile"]
        email = request.form["email"]
        dob = request.form["dob"]
        gender = request.form["gender"]
        occupation = request.form["occupation"]
        address = request.form["address"]
        aadhaar = request.form["aadhaar"]

        nominee_name = request.form["nominee_name"]
        nominee_relation = request.form["nominee_relation"]
        nominee_mobile = request.form["nominee_mobile"]

        remarks = request.form["remarks"]

        photo = request.files.get("photo")

        filename = ""

        if photo and photo.filename:

            filename = secure_filename(photo.filename)

            photo.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )

        conn = get_connection()

        conn.execute("""

        INSERT INTO customers(

            name,
            mobile,
            email,
            dob,
            gender,
            occupation,
            address,
            aadhaar,
            nominee_name,
            nominee_relation,
            nominee_mobile,
            photo,
            remarks

        )

        VALUES(

            ?,?,?,?,?,?,?,?,?,?,?,?,?

        )

        """,

        (

            name,
            mobile,
            email,
            dob,
            gender,
            occupation,
            address,
            aadhaar,
            nominee_name,
            nominee_relation,
            nominee_mobile,
            filename,
            remarks

        )

        )

        conn.commit()

        conn.close()

        return redirect(url_for("customers"))

    return render_template("add_customer.html")

@app.route("/edit_customer/<int:id>", methods=["GET","POST"])
def edit_customer(id):
    conn = get_connection()
    cur = conn.cursor()
    if request.method == "POST":
        cur.execute(
            """UPDATE customers
               SET name=?, mobile=?, address=?, aadhaar=?
               WHERE id=?""",
            (
                request.form["name"],
                request.form["mobile"],
                request.form["address"],
                request.form["aadhaar"],
                id,
            ),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("customers"))
    cur.execute("SELECT * FROM customers WHERE id=?", (id,))
    customer = cur.fetchone()
    conn.close()
    return render_template("edit_customer.html", customer=customer)

@app.route("/delete_customer/<int:id>")
def delete_customer(id):
    conn = get_connection()
    conn.execute("DELETE FROM customers WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("customers"))

@app.route("/add_loan", methods=["GET","POST"])
def add_loan():
    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":

        loan_number = generate_loan_number()

        customer_id = request.form["customer_id"]
        ornament_type = request.form["gold_item"]
        quantity = int(request.form["quantity"])
        description = request.form["description"]

        gross_weight = float(request.form["gross_weight"])
        stone_weight = float(request.form["stone_weight"])
        net_weight = float(request.form["net_weight"])

        purity = request.form["purity"]

        gold_rate = float(request.form["gold_rate"])
        gold_value = float(request.form["gold_value"])
        eligible_amount = float(request.form["eligible_amount"])

        loan_amount = float(request.form.get("loan_amount") or 0)
        interest_rate = float(request.form["interest_rate"])

        loan_date = request.form["loan_date"]
        due_date = request.form["due_date"]

        cur.execute("""
        INSERT INTO loans(

            loan_number,
            customer_id,
            ornament_type,
            quantity,
            description,
            gross_weight,
            stone_weight,
            net_weight,
            purity,
            gold_rate,
            gold_value,
            eligible_amount,
            loan_amount,
            outstanding_amount,
            interest_rate,
            loan_date,
            due_date,
            status

        )

        VALUES(
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )

        """, (

            loan_number,
            customer_id,
            ornament_type,
            quantity,
            description,
            gross_weight,
            stone_weight,
            net_weight,
            purity,
            gold_rate,
            gold_value,
            eligible_amount,
            loan_amount,
            loan_amount,
            interest_rate,
            loan_date,
            due_date,
            "Active"

        ))

        conn.commit()
        conn.close()

        return redirect(url_for("loans"))

    cur.execute("SELECT * FROM customers ORDER BY name")
    customers = cur.fetchall()
    conn.close()
    return render_template(
        "add_loan.html",
        customers=customers,
        loan_number=generate_loan_number()
    )

@app.route("/loans")
def loans():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT l.*, c.name AS customer_name
    FROM loans l
    JOIN customers c ON c.id=l.customer_id
    ORDER BY l.id DESC
    """)
    loans = cur.fetchall()
    conn.close()
    return render_template("loans.html", loans=loans)
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))
@app.route("/admin")
def admin():

    if "user" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        return "Access Denied - Admin Only", 403

    return redirect(url_for("home"))
@app.route("/employee")
def employee():

    if "user" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "employee":
        return "Access Denied - Employee Only", 403

    return redirect(url_for("home"))
if __name__ == "__main__":
    app.run(debug=True)
