"""
Maison Elara — Flask backend
A clean, beginner-friendly e-commerce backend: products, cart, checkout,
accounts, and a small admin panel. SQLite for storage, Stripe for payment,
Cloudinary (optional) for image hosting.
"""

import os
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import stripe

from config import Config
from database import get_db

app = Flask(__name__)
app.config.from_object(Config)
stripe.api_key = app.config["STRIPE_SECRET_KEY"]

# ---- Optional Cloudinary setup -------------------------------------------
CLOUDINARY_ENABLED = bool(
    app.config["CLOUDINARY_CLOUD_NAME"]
    and app.config["CLOUDINARY_API_KEY"]
    and app.config["CLOUDINARY_API_SECRET"]
)
if CLOUDINARY_ENABLED:
    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=app.config["CLOUDINARY_CLOUD_NAME"],
        api_key=app.config["CLOUDINARY_API_KEY"],
        api_secret=app.config["CLOUDINARY_API_SECRET"],
        secure=True,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "error")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def current_user():
    if not session.get("user_id"):
        return None
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    db.close()
    return user


def cart_key(product_id, size, color):
    return f"{product_id}::{size or '-'}::{color or '-'}"


def get_cart_details():
    """Turn the session cart (ids + qty) into full line items with product data."""
    cart = session.get("cart", {})
    if not cart:
        return [], 0.0

    db = get_db()
    items = []
    total = 0.0
    for key, entry in cart.items():
        product = db.execute("SELECT * FROM products WHERE id = ?", (entry["product_id"],)).fetchone()
        if not product:
            continue
        subtotal = product["price"] * entry["qty"]
        total += subtotal
        items.append({
            "key": key,
            "product": product,
            "qty": entry["qty"],
            "size": entry.get("size", ""),
            "color": entry.get("color", ""),
            "subtotal": subtotal,
        })
    db.close()
    return items, round(total, 2)


@app.context_processor
def inject_globals():
    cart = session.get("cart", {})
    cart_count = sum(item["qty"] for item in cart.values())
    return {
        "store_name": app.config["STORE_NAME"],
        "cart_count": cart_count,
        "user": current_user(),
        "stripe_publishable_key": app.config["STRIPE_PUBLISHABLE_KEY"],
    }


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    db = get_db()
    featured = db.execute("SELECT * FROM products WHERE is_featured = 1 LIMIT 4").fetchall()
    clothing = db.execute("SELECT * FROM products WHERE category = 'Clothing' LIMIT 4").fetchall()
    jewellery = db.execute("SELECT * FROM products WHERE category = 'Jewellery' LIMIT 4").fetchall()
    new_arrivals = db.execute("SELECT * FROM products WHERE is_new_arrival = 1 LIMIT 4").fetchall()
    best_sellers = db.execute("SELECT * FROM products WHERE is_best_seller = 1 LIMIT 4").fetchall()
    reviews = db.execute("SELECT * FROM reviews ORDER BY id DESC LIMIT 6").fetchall()
    db.close()
    return render_template(
        "index.html",
        featured=featured, clothing=clothing, jewellery=jewellery,
        new_arrivals=new_arrivals, best_sellers=best_sellers, reviews=reviews,
    )


@app.route("/shop")
def shop():
    category = request.args.get("category", "").strip()
    search = request.args.get("q", "").strip()

    db = get_db()
    query = "SELECT * FROM products WHERE 1=1"
    params = []
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
    if search:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    query += " ORDER BY created_at DESC"
    products = db.execute(query, params).fetchall()
    db.close()

    return render_template(
        "shop.html", products=products, active_category=category or "All", search=search
    )


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        db.close()
        abort(404)
    related = db.execute(
        "SELECT * FROM products WHERE category = ? AND id != ? LIMIT 4",
        (product["category"], product_id),
    ).fetchall()
    db.close()

    sizes = [s.strip() for s in (product["sizes"] or "").split(",") if s.strip()]
    colors = [c.strip() for c in (product["colors"] or "").split(",") if c.strip()]
    gallery = [g.strip() for g in (product["gallery"] or "").split(",") if g.strip()]

    return render_template(
        "product.html", product=product, related=related,
        sizes=sizes, colors=colors, gallery=gallery,
    )


# ---------------------------------------------------------------------------
# Cart
# ---------------------------------------------------------------------------

@app.route("/cart")
def cart_view():
    items, total = get_cart_details()
    return render_template("cart.html", items=items, total=total)


@app.route("/cart/add", methods=["POST"])
def cart_add():
    product_id = request.form.get("product_id", type=int)
    size = request.form.get("size", "")
    color = request.form.get("color", "")
    qty = request.form.get("qty", 1, type=int) or 1

    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    db.close()
    if not product:
        flash("That product could not be found.", "error")
        return redirect(url_for("shop"))

    cart = session.get("cart", {})
    key = cart_key(product_id, size, color)
    if key in cart:
        cart[key]["qty"] += qty
    else:
        cart[key] = {"product_id": product_id, "qty": qty, "size": size, "color": color}
    session["cart"] = cart
    flash(f"Added {product['name']} to your bag.", "success")

    if request.form.get("buy_now"):
        return redirect(url_for("checkout"))
    return redirect(request.referrer or url_for("shop"))


@app.route("/cart/update", methods=["POST"])
def cart_update():
    key = request.form.get("key")
    qty = request.form.get("qty", 1, type=int)
    cart = session.get("cart", {})
    if key in cart:
        if qty and qty > 0:
            cart[key]["qty"] = qty
        else:
            cart.pop(key, None)
    session["cart"] = cart
    return redirect(url_for("cart_view"))


@app.route("/cart/remove", methods=["POST"])
def cart_remove():
    key = request.form.get("key")
    cart = session.get("cart", {})
    cart.pop(key, None)
    session["cart"] = cart
    return redirect(url_for("cart_view"))


# ---------------------------------------------------------------------------
# Checkout + Stripe payment
# ---------------------------------------------------------------------------

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    items, total = get_cart_details()
    if not items:
        flash("Your bag is empty.", "error")
        return redirect(url_for("shop"))

    if request.method == "GET":
        return render_template("checkout.html", items=items, total=total)

    # POST: create a pending order, then redirect the customer to Stripe Checkout
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()
    city = request.form.get("city", "").strip()
    postal_code = request.form.get("postal_code", "").strip()
    country = request.form.get("country", "").strip()

    if not all([name, email, address, city, postal_code, country]):
        flash("Please fill in every shipping field.", "error")
        return render_template("checkout.html", items=items, total=total)

    db = get_db()
    cur = db.execute(
        """INSERT INTO orders (user_id, customer_name, email, address, city, postal_code, country, total_price, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')""",
        (session.get("user_id"), name, email, address, city, postal_code, country, total),
    )
    order_id = cur.lastrowid
    for item in items:
        db.execute(
            """INSERT INTO order_items (order_id, product_id, name, price, quantity, size, color)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (order_id, item["product"]["id"], item["product"]["name"], item["product"]["price"],
             item["qty"], item["size"], item["color"]),
        )
    db.commit()

    # If Stripe isn't configured yet, let developers still test the flow end-to-end.
    if not app.config["STRIPE_SECRET_KEY"]:
        db.execute("UPDATE orders SET status = 'paid' WHERE id = ?", (order_id,))
        db.commit()
        db.close()
        session["cart"] = {}
        flash("Stripe is not configured yet, so this test order was marked paid automatically.", "success")
        return redirect(url_for("order_confirmation", order_id=order_id))

    line_items = [{
        "price_data": {
            "currency": app.config["CURRENCY"],
            "product_data": {"name": item["product"]["name"]},
            "unit_amount": int(round(item["product"]["price"] * 100)),
        },
        "quantity": item["qty"],
    } for item in items]

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            customer_email=email,
            success_url=url_for("checkout_success", _external=True) + f"?order_id={order_id}&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=url_for("checkout_cancel", _external=True) + f"?order_id={order_id}",
        )
    except Exception as exc:
        db.close()
        flash(f"Payment could not be started: {exc}", "error")
        return render_template("checkout.html", items=items, total=total)

    db.execute("UPDATE orders SET stripe_session_id = ? WHERE id = ?", (checkout_session.id, order_id))
    db.commit()
    db.close()

    return redirect(checkout_session.url, code=303)


@app.route("/checkout/success")
def checkout_success():
    order_id = request.args.get("order_id", type=int)
    session_id = request.args.get("session_id")

    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        db.close()
        abort(404)

    # Confirm the payment actually succeeded before marking the order paid
    if session_id and app.config["STRIPE_SECRET_KEY"]:
        try:
            checkout_session = stripe.checkout.Session.retrieve(session_id)
            if checkout_session.payment_status == "paid":
                db.execute("UPDATE orders SET status = 'paid' WHERE id = ?", (order_id,))
                # reduce stock for each item
                items = db.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
                for item in items:
                    if item["product_id"]:
                        db.execute(
                            "UPDATE products SET stock = MAX(0, stock - ?) WHERE id = ?",
                            (item["quantity"], item["product_id"]),
                        )
                db.commit()
        except Exception:
            pass

    db.close()
    session["cart"] = {}
    return redirect(url_for("order_confirmation", order_id=order_id))


@app.route("/checkout/cancel")
def checkout_cancel():
    order_id = request.args.get("order_id", type=int)
    db = get_db()
    if order_id:
        db.execute("UPDATE orders SET status = 'cancelled' WHERE id = ? AND status = 'pending'", (order_id,))
        db.commit()
    db.close()
    flash("Your payment was cancelled. Your bag has been kept for you.", "error")
    return redirect(url_for("cart_view"))


@app.route("/order/<int:order_id>")
def order_confirmation(order_id):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        db.close()
        abort(404)
    items = db.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
    db.close()
    return render_template("order_confirmation.html", order=order, items=items)


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or len(password) < 6:
            flash("Please provide your name, a valid email, and a password of at least 6 characters.", "error")
            return render_template("register.html")

        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            db.close()
            flash("An account with that email already exists.", "error")
            return render_template("register.html")

        db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        db.commit()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        db.close()

        session["user_id"] = user["id"]
        session["is_admin"] = bool(user["is_admin"])
        flash(f"Welcome to Maison Elara, {name}.", "success")
        return redirect(url_for("home"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        db.close()

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Incorrect email or password.", "error")
            return render_template("login.html")

        session["user_id"] = user["id"]
        session["is_admin"] = bool(user["is_admin"])
        flash(f"Welcome back, {user['name']}.", "success")
        return redirect(request.args.get("next") or url_for("home"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("home"))


# ---------------------------------------------------------------------------
# Newsletter
# ---------------------------------------------------------------------------

@app.route("/newsletter", methods=["POST"])
def newsletter_signup():
    email = request.form.get("email", "").strip().lower()
    if email:
        db = get_db()
        try:
            db.execute("INSERT INTO newsletter_signups (email) VALUES (?)", (email,))
            db.commit()
            flash("You're on the list. Welcome to the house of Elara.", "success")
        except Exception:
            flash("You're already subscribed.", "success")
        db.close()
    return redirect(request.referrer or url_for("home"))


# ---------------------------------------------------------------------------
# Admin panel
# ---------------------------------------------------------------------------

@app.route("/admin")
@admin_required
def admin_dashboard():
    db = get_db()
    products = db.execute("SELECT * FROM products ORDER BY created_at DESC").fetchall()
    orders = db.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 5").fetchall()
    stats = {
        "product_count": db.execute("SELECT COUNT(*) c FROM products").fetchone()["c"],
        "order_count": db.execute("SELECT COUNT(*) c FROM orders").fetchone()["c"],
        "revenue": db.execute("SELECT COALESCE(SUM(total_price),0) s FROM orders WHERE status = 'paid'").fetchone()["s"],
    }
    db.close()
    return render_template("admin/dashboard.html", products=products, orders=orders, stats=stats)


def handle_image_upload():
    """Upload to Cloudinary if a file was given and Cloudinary is configured.
    Falls back to a plain image URL field. Returns the final image URL or None."""
    image_url = request.form.get("image_url", "").strip()
    file = request.files.get("image_file")

    if file and file.filename:
        if CLOUDINARY_ENABLED:
            result = cloudinary.uploader.upload(file, folder="maison_elara/products")
            return result["secure_url"]
        else:
            # No Cloudinary configured: save locally as a simple fallback
            filename = secure_filename(file.filename)
            local_dir = os.path.join(app.static_folder, "images", "products")
            os.makedirs(local_dir, exist_ok=True)
            file.save(os.path.join(local_dir, filename))
            return url_for("static", filename=f"images/products/{filename}")

    return image_url or None


@app.route("/admin/products/add", methods=["GET", "POST"])
@admin_required
def admin_add_product():
    if request.method == "POST":
        image_url = handle_image_upload()
        if not image_url:
            flash("Please provide a product image (upload a file or paste a URL).", "error")
            return render_template("admin/add_product.html")

        db = get_db()
        db.execute(
            """INSERT INTO products (name, description, price, category, image_url, stock,
                                      sizes, colors, is_featured, is_new_arrival, is_best_seller)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                request.form.get("name", "").strip(),
                request.form.get("description", "").strip(),
                request.form.get("price", 0, type=float),
                request.form.get("category", "Clothing"),
                image_url,
                request.form.get("stock", 0, type=int),
                request.form.get("sizes", "").strip(),
                request.form.get("colors", "").strip(),
                1 if request.form.get("is_featured") else 0,
                1 if request.form.get("is_new_arrival") else 0,
                1 if request.form.get("is_best_seller") else 0,
            ),
        )
        db.commit()
        db.close()
        flash("Product added.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin/add_product.html")


@app.route("/admin/products/edit/<int:product_id>", methods=["GET", "POST"])
@admin_required
def admin_edit_product(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        db.close()
        abort(404)

    if request.method == "POST":
        image_url = handle_image_upload() or product["image_url"]
        db.execute(
            """UPDATE products SET name=?, description=?, price=?, category=?, image_url=?, stock=?,
                                    sizes=?, colors=?, is_featured=?, is_new_arrival=?, is_best_seller=?
               WHERE id=?""",
            (
                request.form.get("name", "").strip(),
                request.form.get("description", "").strip(),
                request.form.get("price", 0, type=float),
                request.form.get("category", "Clothing"),
                image_url,
                request.form.get("stock", 0, type=int),
                request.form.get("sizes", "").strip(),
                request.form.get("colors", "").strip(),
                1 if request.form.get("is_featured") else 0,
                1 if request.form.get("is_new_arrival") else 0,
                1 if request.form.get("is_best_seller") else 0,
                product_id,
            ),
        )
        db.commit()
        db.close()
        flash("Product updated.", "success")
        return redirect(url_for("admin_dashboard"))

    db.close()
    return render_template("admin/edit_product.html", product=product)


@app.route("/admin/products/delete/<int:product_id>", methods=["POST"])
@admin_required
def admin_delete_product(product_id):
    db = get_db()
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    db.close()
    flash("Product deleted.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/orders")
@admin_required
def admin_orders():
    db = get_db()
    orders = db.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    orders_with_items = []
    for order in orders:
        line_items = db.execute("SELECT * FROM order_items WHERE order_id = ?", (order["id"],)).fetchall()
        orders_with_items.append({"order": order, "line_items": line_items})
    db.close()
    return render_template("admin/orders.html", orders=orders_with_items)


@app.route("/admin/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def admin_update_order_status(order_id):
    new_status = request.form.get("status")
    if new_status in ("pending", "paid", "shipped", "cancelled"):
        db = get_db()
        db.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
        db.commit()
        db.close()
        flash("Order status updated.", "success")
    return redirect(url_for("admin_orders"))


# ---------------------------------------------------------------------------
# Error pages
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403


if __name__ == "__main__":
    if not os.path.exists(app.config["DATABASE"]):
        print("No database found. Run 'python database.py' first to create it.")
    app.run(debug=app.config["DEBUG"])
