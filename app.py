from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"


# =========================
# DATABASE
# =========================
def get_db_connection():
    conn = sqlite3.connect("store.db")
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# CREATE TABLES
# =========================
def create_tables():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            image TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            product_name TEXT NOT NULL,
            price INTEGER NOT NULL,
            image TEXT NOT NULL,
            quantity INTEGER DEFAULT 1
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            product_name TEXT NOT NULL,
            price INTEGER NOT NULL,
            image TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


create_tables()


# =========================
# ADMIN DECORATOR
# =========================
def admin_required(func):
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            return redirect("/login")

        if session.get("role") != "admin":
            return "Access Denied"

        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    return wrapper


# =========================
# HOME
# =========================
@app.route("/")
def home():
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return render_template("index.html", products=products)


# =========================
# ADMIN CREATE (ONE TIME)
# =========================
@app.route("/create-admin")
def create_admin():
    conn = get_db_connection()

    conn.execute("""
        INSERT INTO users (username, email, password, role)
        VALUES (?, ?, ?, ?)
    """, ("admin", "admin@gmail.com", "1234", "admin"))

    conn.commit()
    conn.close()

    return "Admin Created"


# =========================
# ADMIN PAGE
# =========================
@app.route("/admin")
@admin_required
def admin():
    return render_template("admin.html")


# =========================
# ADD PRODUCT
# =========================
@app.route("/add-product", methods=["GET", "POST"])
@admin_required
def add_product():

    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        image = request.form["image"]

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO products (name, price, image) VALUES (?, ?, ?)",
            (name, price, image)
        )
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("add_product.html")


# =========================
# DELETE PRODUCT
# =========================
@app.route("/delete-product/<int:id>")
@admin_required
def delete_product(id):

    conn = get_db_connection()
    conn.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/")


# =========================
# EDIT PRODUCT
# =========================
@app.route("/edit-product/<int:id>")
@admin_required
def edit_product(id):

    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id=?", (id,)).fetchone()
    conn.close()

    return render_template("edit.html", product=product)


# =========================
# UPDATE PRODUCT
# =========================
@app.route("/update-product/<int:id>", methods=["POST"])
@admin_required
def update_product(id):

    name = request.form["name"]
    price = request.form["price"]
    image = request.form["image"]

    conn = get_db_connection()
    conn.execute("""
        UPDATE products
        SET name=?, price=?, image=?
        WHERE id=?
    """, (name, price, image, id))

    conn.commit()
    conn.close()

    return redirect("/")


# =========================
# REGISTER
# =========================
@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/register-user", methods=["POST"])
def register_user():

    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]

    conn = get_db_connection()

    existing = conn.execute(
        "SELECT * FROM users WHERE email=?",
        (email,)
    ).fetchone()

    if existing:
        return "Email already exists"

    conn.execute(
        "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
        (username, email, password, "user")
    )

    conn.commit()
    conn.close()

    return redirect("/login")


# =========================
# LOGIN
# =========================
@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/login-user", methods=["POST"])
def login_user():

    email = request.form["email"]
    password = request.form["password"]

    conn = get_db_connection()

    user = conn.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, password)
    ).fetchone()

    conn.close()

    if user:
        session["user"] = user["username"]
        session["role"] = user["role"]
        session["email"] = user["email"]

        return redirect("/")

    return "Invalid Credentials"


# =========================
# CART
# =========================
@app.route("/cart")
def cart():

    if not session.get("user"):
        return redirect("/login")

    conn = get_db_connection()

    items = conn.execute(
        "SELECT * FROM cart WHERE username=?",
        (session["user"],)
    ).fetchall()

    conn.close()

    return render_template("cart.html", items=items)


@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():

    if not session.get("user"):
        return {"message": "Login required"}

    data = request.json

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO cart (username, product_name, price, image, quantity)
        VALUES (?, ?, ?, ?, ?)
    """, (
        session["user"],
        data["name"],
        data["price"],
        data["image"],
        1
    ))

    conn.commit()
    conn.close()

    return {"message": "Added to cart"}


# =========================
# PLACE ORDER
# =========================
@app.route("/place-order", methods=["POST"])
def place_order():

    if not session.get("user"):
        return {"message": "Login Required"}

    data = request.json
    username = session["user"]

    conn = get_db_connection()

    for item in data:
       conn.execute("""
    INSERT INTO orders (username, product_name, price, image, status)
    VALUES (?, ?, ?, ?, ?)
""", (username, item["name"], item["price"], item["image"], "Processing"))

    conn.commit()
    conn.close()

    return {"message": "Order Placed"}


# =========================
# ORDERS
# =========================
@app.route("/orders")
def orders():

    if not session.get("user"):
        return redirect("/login")

    conn = get_db_connection()

    orders = conn.execute(
        "SELECT * FROM orders WHERE username=?",
        (session["user"],)
    ).fetchall()

    conn.close()

    return render_template("orders.html", orders=orders)


# =========================
# INVOICE
# =========================
@app.route("/invoice/<int:order_id>")
def invoice(order_id):

    conn = get_db_connection()

    order = conn.execute(
        "SELECT * FROM orders WHERE id=?",
        (order_id,)
    ).fetchone()

    conn.close()

    if not order:
        return "Order not found"

    return render_template("invoice.html", order=order)


# =========================
# SEARCH
# =========================
@app.route("/search")
def search():

    query = request.args.get("q")

    conn = get_db_connection()

    products = conn.execute(
        "SELECT * FROM products WHERE name LIKE ?",
        ('%' + query + '%',)
    ).fetchall()

    conn.close()

    return render_template("index.html", products=products)


# =========================
# PAYMENT
# =========================
@app.route("/payment")
def payment():

    if not session.get("user"):
        return redirect("/login")

    conn = get_db_connection()

    items = conn.execute(
        "SELECT * FROM cart WHERE username=?",
        (session["user"],)
    ).fetchall()

    total = sum([i["price"] for i in items])

    conn.close()

    return render_template("payment.html", total=total)


# =========================
# DEBUG USERS
# =========================
@app.route("/debug-users")
def debug_users():

    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()

    return {"users": [dict(u) for u in users]}


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)