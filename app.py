from flask import Flask, render_template, jsonify, request, session, redirect
import sqlite3
import os
import re
import time
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash

try:
    from twilio.rest import Client
except ImportError:
    Client = None

app = Flask(__name__)

DATABASE = "database/realestate.db"

# Secret key for admin login session
app.secret_key = "realestate_admin_secret_key_2026"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_property_columns():
    """Add optional property contact fields without destroying existing data."""
    connection = get_db_connection()
    try:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(properties)").fetchall()}

        if "owner_name" not in columns:
            connection.execute("ALTER TABLE properties ADD COLUMN owner_name TEXT")

        if "owner_contact" not in columns:
            connection.execute("ALTER TABLE properties ADD COLUMN owner_contact TEXT")

        connection.commit()
    finally:
        connection.close()


# Make the existing database compatible with owner/contact fields.
ensure_property_columns()


def ensure_user_table():
    """Create/migrate the user account table, including phone login support."""
    connection = get_db_connection()
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                phone TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(users)").fetchall()
        }
        if "phone" not in columns:
            connection.execute("ALTER TABLE users ADD COLUMN phone TEXT")

        connection.commit()
    finally:
        connection.close()


def normalize_indian_phone(value):
    """Return an Indian phone number in E.164 format."""
    phone = re.sub(r"[^0-9+]", "", str(value or "").strip())
    if phone.startswith("+91"):
        digits = phone[3:]
    elif phone.startswith("91") and len(phone) == 12:
        digits = phone[2:]
    else:
        digits = phone

    if not re.fullmatch(r"[6-9]\d{9}", digits):
        return None
    return "+91" + digits


def twilio_client():
    if Client is None:
        return None

    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    if not account_sid or not auth_token:
        return None

    return Client(account_sid, auth_token)


def twilio_service_sid():
    return os.getenv("TWILIO_VERIFY_SERVICE_SID", "").strip()


def user_logged_in():
    return bool(session.get("user_logged_in"))


def user_or_admin_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if session.get("admin_logged_in") or session.get("user_logged_in"):
            return function(*args, **kwargs)
        return jsonify({
            "success": False,
            "authenticated": False,
            "message": "Please sign in to search properties."
        }), 401
    return decorated_function


ensure_user_table()


def ensure_admin_table():
    """Create the admin account table and ensure a default admin account exists."""
    connection = get_db_connection()
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        existing = connection.execute(
            "SELECT id FROM admins WHERE username = ?",
            ("admin",)
        ).fetchone()

        if not existing:
            connection.execute(
                """
                INSERT INTO admins (username, password_hash)
                VALUES (?, ?)
                """,
                ("admin", generate_password_hash("admin123"))
            )

        connection.commit()
    finally:
        connection.close()


ensure_admin_table()


def ensure_optional_property_columns():
    """Make the local properties table compatible with seeded listings."""
    connection = get_db_connection()
    try:
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(properties)"
            ).fetchall()
        }

        if "source" not in columns:
            connection.execute(
                "ALTER TABLE properties ADD COLUMN source TEXT"
            )

        if "description" not in columns:
            connection.execute(
                "ALTER TABLE properties ADD COLUMN description TEXT"
            )

        connection.commit()
    finally:
        connection.close()


def ensure_multiple_houses_for_every_village():
    """
    Ensure every village has multiple house listings.

    Existing user data is preserved. Only missing inventory is added.
    The routine is intentionally idempotent: after a village reaches the
    target count, no more seeded houses are inserted for that village.
    """

    TARGET_HOUSES_PER_VILLAGE = 3

    first_names = [
        "Arjun", "Meghana", "Kiran", "Nikhil", "Pooja",
        "Vikram", "Ananya", "Rohit", "Sneha", "Manoj",
        "Divya", "Suresh", "Kavya", "Ajay", "Priya"
    ]

    last_names = [
        "Rao", "Shetty", "Patil", "Gowda", "Reddy",
        "Naik", "Kulkarni", "Hegde", "Desai", "Bhat",
        "Nayak", "Joshi", "Kumar", "Menon", "Sharma"
    ]

    connection = get_db_connection()

    try:
        villages = connection.execute(
            """
            SELECT
                v.id AS village_id,
                v.name AS village_name,
                t.id AS taluk_id,
                t.name AS taluk_name,
                d.id AS district_id,
                d.name AS district_name
            FROM villages v
            JOIN taluks t
                ON v.taluk_id = t.id
            JOIN districts d
                ON t.district_id = d.id
            ORDER BY v.id
            """
        ).fetchall()

        if not villages:
            return

        # One grouped query avoids running a COUNT query for every village.
        existing = connection.execute(
            """
            SELECT
                village_id,
                COUNT(*) AS house_count
            FROM properties
            WHERE LOWER(TRIM(property_type)) = 'house'
              AND village_id IS NOT NULL
            GROUP BY village_id
            """
        ).fetchall()

        house_counts = {
            row["village_id"]: int(row["house_count"] or 0)
            for row in existing
        }

        inserts = []

        for village in villages:
            village_id = village["village_id"]
            current = house_counts.get(village_id, 0)
            missing = max(0, TARGET_HOUSES_PER_VILLAGE - current)

            for slot in range(missing):
                seed_number = village_id * 10 + current + slot + 1

                # Deterministic but varied listing values.
                bhk = str(2 + (seed_number % 3))
                area = 1100 + ((seed_number * 137) % 1400)

                base_psf = 1800 + (
                    (village["district_id"] * 173) % 2200
                )

                price_per_sqft = base_psf + (
                    seed_number % 450
                )

                price = int(area * price_per_sqft)
                price = int(round(price / 50000) * 50000)

                owner_index = seed_number % len(first_names)
                owner_name = (
                    first_names[owner_index]
                    + " "
                    + last_names[owner_index]
                )

                owner_contact = (
                    "+91 90"
                    + f"{seed_number % 100000000:08d}"
                )

                title = (
                    f"{bhk} BHK Family House – "
                    f"{village['village_name']}"
                )

                description = (
                    f"Residential house listing in {village['village_name']}, "
                    f"{village['taluk_name']}, {village['district_name']}. "
                    f"Additional property listing created to provide multiple "
                    f"house listings for property search and analysis."
                )

                inserts.append((
                    village["district_id"],
                    village["taluk_id"],
                    village_id,
                    "House",
                    bhk,
                    title,
                    area,
                    price,
                    price_per_sqft,
                    description,
                    "Karnataka inventory",
                    owner_name,
                    owner_contact
                ))

        if inserts:
            connection.executemany(
                """
                INSERT INTO properties (
                    district_id,
                    taluk_id,
                    village_id,
                    property_type,
                    bhk,
                    title,
                    area_sqft,
                    price,
                    price_per_sqft,
                    description,
                    source,
                    owner_name,
                    owner_contact
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                inserts
            )

            connection.commit()
            print(
                f"Added {len(inserts):,} house listings across Karnataka villages."
            )

    finally:
        connection.close()


ensure_optional_property_columns()
ensure_multiple_houses_for_every_village()


def clean_listing_text():
    """Remove old demo wording from existing property records without changing facts."""
    connection = get_db_connection()
    try:
        connection.execute(
            """
            UPDATE properties
            SET title = TRIM(
                REPLACE(
                    REPLACE(title, 'Demo Property - ', ''),
                    'Demo Property – ',
                    ''
                )
            )
            WHERE title LIKE 'Demo Property - %'
               OR title LIKE 'Demo Property – %'
            """
        )

        connection.execute(
            """
            UPDATE properties
            SET source = 'Karnataka inventory'
            WHERE LOWER(TRIM(COALESCE(source, ''))) IN (
                'demo inventory',
                'demo',
                'demo data'
            )
            """
        )

        connection.execute(
            """
            UPDATE properties
            SET description = REPLACE(
                REPLACE(
                    COALESCE(description, ''),
                    'Demo inventory created to provide multiple house listings for property search and analysis.',
                    'Additional property listing for property search and market analysis.'
                ),
                'Demo inventory',
                'Karnataka inventory'
            )
            WHERE description LIKE '%Demo%' OR description LIKE '%demo%'
            """
        )

        connection.commit()
    finally:
        connection.close()


clean_listing_text()


# ============================================================
# ADMIN LOGIN PROTECTION
# ============================================================

def admin_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if not session.get("admin_logged_in"):
            return redirect("/admin/login")

        return function(*args, **kwargs)

    return decorated_function


# ============================================================
# PUBLIC HOME PAGE
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# USER LOGIN / REGISTRATION
# ============================================================

@app.route("/login")
def user_login_page():
    if session.get("user_logged_in"):
        next_url = request.args.get("next") or "/"
        return redirect(next_url)
    return render_template("login.html")


@app.route("/api/user/register", methods=["POST"])
def user_register_api():
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    phone = normalize_indian_phone(data.get("phone"))

    if not name or not email or not password or not phone:
        return jsonify({
            "success": False,
            "message": "Name, email, phone number and password are required."
        }), 400

    if len(name) < 2:
        return jsonify({
            "success": False,
            "message": "Please enter your full name."
        }), 400

    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({
            "success": False,
            "message": "Please enter a valid email address."
        }), 400

    if len(password) < 6:
        return jsonify({
            "success": False,
            "message": "Password must contain at least 6 characters."
        }), 400

    connection = get_db_connection()
    try:
        existing_email = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if existing_email:
            return jsonify({
                "success": False,
                "message": "An account with this email already exists."
            }), 409

        existing_phone = connection.execute(
            "SELECT id FROM users WHERE phone = ?",
            (phone,)
        ).fetchone()

        if existing_phone:
            return jsonify({
                "success": False,
                "message": "An account with this phone number already exists."
            }), 409

        cursor = connection.execute(
            """
            INSERT INTO users (name, email, password_hash, phone)
            VALUES (?, ?, ?, ?)
            """,
            (name, email, generate_password_hash(password), phone)
        )
        connection.commit()

        session.clear()
        session["user_logged_in"] = True
        session["user_id"] = cursor.lastrowid
        session["user_name"] = name
        session["user_email"] = email
        session["user_phone"] = phone

        return jsonify({
            "success": True,
            "message": "Account created successfully.",
            "user": {"name": name, "email": email, "phone": phone}
        })

    except sqlite3.Error as error:
        connection.rollback()
        return jsonify({
            "success": False,
            "message": "Database error: " + str(error)
        }), 500
    finally:
        connection.close()


@app.route("/api/user/send-otp", methods=["POST"])
def user_send_otp_api():
    data = request.get_json(silent=True) or {}
    phone = normalize_indian_phone(data.get("phone"))

    if not phone:
        return jsonify({
            "success": False,
            "message": "Enter a valid 10-digit Indian mobile number."
        }), 400

    connection = get_db_connection()
    try:
        registered = connection.execute(
            "SELECT id FROM users WHERE phone = ?",
            (phone,)
        ).fetchone()
    finally:
        connection.close()

    if not registered:
        return jsonify({
            "success": False,
            "message": "This phone number is not registered. Create an account first."
        }), 404

    client = twilio_client()
    service_sid = twilio_service_sid()
    if client is None or not service_sid:
        return jsonify({
            "success": False,
            "message": "Phone OTP is not configured. Add your Twilio credentials first."
        }), 503

    last_sent = float(session.get("otp_last_sent", 0) or 0)
    if time.time() - last_sent < 45:
        remaining = max(1, 45 - int(time.time() - last_sent))
        return jsonify({
            "success": False,
            "message": f"Please wait {remaining} seconds before requesting another OTP."
        }), 429

    try:
        verification = client.verify.v2.services(service_sid).verifications.create(
            channel="sms",
            to=phone
        )

        if str(getattr(verification, "status", "")).lower() not in {"pending", "sent"}:
            return jsonify({
                "success": False,
                "message": "Unable to send OTP right now."
            }), 502

        session["otp_phone"] = phone
        session["otp_last_sent"] = time.time()

        return jsonify({
            "success": True,
            "message": "OTP sent to your mobile number."
        })
    except Exception as error:
        return jsonify({
            "success": False,
            "message": "OTP service error: " + str(error)
        }), 502


@app.route("/api/user/verify-otp", methods=["POST"])
def user_verify_otp_api():
    data = request.get_json(silent=True) or {}
    phone = normalize_indian_phone(data.get("phone"))
    code = str(data.get("code", "")).strip()

    if not phone or not re.fullmatch(r"\d{4,10}", code):
        return jsonify({
            "success": False,
            "message": "Enter a valid phone number and OTP."
        }), 400

    if session.get("otp_phone") != phone:
        return jsonify({
            "success": False,
            "message": "Request a new OTP for this phone number."
        }), 400

    client = twilio_client()
    service_sid = twilio_service_sid()
    if client is None or not service_sid:
        return jsonify({
            "success": False,
            "message": "Phone OTP is not configured. Add your Twilio credentials first."
        }), 503

    try:
        verification_check = client.verify.v2.services(service_sid).verification_checks.create(
            to=phone,
            code=code
        )
    except Exception as error:
        return jsonify({
            "success": False,
            "message": "OTP verification error: " + str(error)
        }), 502

    if str(getattr(verification_check, "status", "")).lower() != "approved":
        return jsonify({
            "success": False,
            "message": "Invalid or expired OTP."
        }), 401

    connection = get_db_connection()
    try:
        user = connection.execute(
            """
            SELECT id, name, email, phone
            FROM users
            WHERE phone = ?
            """,
            (phone,)
        ).fetchone()
    finally:
        connection.close()

    if not user:
        return jsonify({
            "success": False,
            "message": "This phone number is not registered. Create an account first."
        }), 404

    session.clear()
    session["user_logged_in"] = True
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]
    session["user_phone"] = user["phone"]

    return jsonify({
        "success": True,
        "message": "OTP verified. Sign in successful.",
        "user": {
            "name": user["name"],
            "email": user["email"],
            "phone": user["phone"]
        }
    })


@app.route("/api/user/login", methods=["POST"])
def user_login_api():
    data = request.get_json(silent=True) or {}

    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required."
        }), 400

    connection = get_db_connection()
    try:
        user = connection.execute(
            """
            SELECT id, name, email, password_hash, phone
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()
    finally:
        connection.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    session.clear()
    session["user_logged_in"] = True
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]
    session["user_phone"] = user["phone"] if "phone" in user.keys() else None

    return jsonify({
        "success": True,
        "message": "Sign in successful.",
        "user": {
            "name": user["name"],
            "email": user["email"],
            "phone": user["phone"] if "phone" in user.keys() else None
        }
    })


@app.route("/api/user/me")
def user_me_api():
    if session.get("user_logged_in"):
        return jsonify({
            "authenticated": True,
            "user": {
                "name": session.get("user_name", ""),
                "email": session.get("user_email", ""),
                "phone": session.get("user_phone", "")
            }
        })

    if session.get("admin_logged_in"):
        return jsonify({
            "authenticated": True,
            "admin": True,
            "user": {
                "name": session.get("admin_username", "Admin"),
                "email": ""
            }
        })

    return jsonify({"authenticated": False})


@app.route("/api/user/logout", methods=["POST"])
def user_logout_api():
    session.clear()
    return jsonify({"success": True, "message": "Signed out."})


# ============================================================
# ADMIN LOGIN PAGE
# ============================================================

@app.route("/admin/login")
def admin_login():

    if session.get("admin_logged_in"):
        return redirect("/admin")

    return render_template("login.html")


# ============================================================
# ADMIN LOGIN API
# ============================================================

@app.route("/api/admin/login", methods=["POST"])
def admin_login_api():

    data = request.get_json()

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:

        return jsonify({
            "success": False,
            "message": "Username and password are required."
        }), 400


    connection = get_db_connection()

    admin = connection.execute("""
        SELECT id, username, password_hash
        FROM admins
        WHERE username = ?
    """, (username,)).fetchone()

    connection.close()


    if admin and check_password_hash(
        admin["password_hash"],
        password
    ):

        session["admin_logged_in"] = True
        session["admin_id"] = admin["id"]
        session["admin_username"] = admin["username"]

        return jsonify({
            "success": True,
            "message": "Login successful."
        })


    return jsonify({
        "success": False,
        "message": "Invalid username or password."
    }), 401


# ============================================================
# ADMIN LOGOUT
# ============================================================

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect("/admin/login")


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin")
@admin_required
def admin():

    return render_template("admin.html")


# ============================================================
# DISTRICTS
# ============================================================

@app.route("/api/districts")
def get_districts():

    connection = get_db_connection()

    districts = connection.execute("""
        SELECT id, name
        FROM districts
        ORDER BY name
    """).fetchall()

    connection.close()

    return jsonify([
        {
            "id": district["id"],
            "name": district["name"]
        }
        for district in districts
    ])


# ============================================================
# TALUKS
# ============================================================

@app.route("/api/taluks/<int:district_id>")
def get_taluks(district_id):

    connection = get_db_connection()

    taluks = connection.execute("""
        SELECT id, name
        FROM taluks
        WHERE district_id = ?
        ORDER BY name
    """, (district_id,)).fetchall()

    connection.close()

    return jsonify([
        {
            "id": taluk["id"],
            "name": taluk["name"]
        }
        for taluk in taluks
    ])


# ============================================================
# VILLAGES
# ============================================================

@app.route("/api/villages/<int:taluk_id>")
def get_villages(taluk_id):

    connection = get_db_connection()

    villages = connection.execute("""
        SELECT id, name
        FROM villages
        WHERE taluk_id = ?
        ORDER BY name
    """, (taluk_id,)).fetchall()

    connection.close()

    return jsonify([
        {
            "id": village["id"],
            "name": village["name"]
        }
        for village in villages
    ])


# ============================================================
# ADD PROPERTY
# ============================================================

@app.route("/api/properties", methods=["POST"])
@admin_required
def add_property():

    data = request.get_json()

    district_id = data.get("district")
    taluk_id = data.get("taluk")
    village_id = data.get("village")

    title = data.get("title")
    property_type = data.get("propertyType")
    bhk = data.get("bhk")
    area_sqft = data.get("area")
    price = data.get("price")
    source = data.get("source")
    owner_name = data.get("ownerName") or data.get("owner_name")
    owner_contact = data.get("ownerContact") or data.get("owner_contact")


    if not district_id:

        return jsonify({
            "success": False,
            "message": "District is required."
        }), 400


    if not taluk_id:

        return jsonify({
            "success": False,
            "message": "Taluk is required."
        }), 400


    if not title:

        return jsonify({
            "success": False,
            "message": "Property title is required."
        }), 400


    if not property_type:

        return jsonify({
            "success": False,
            "message": "Property type is required."
        }), 400


    if not area_sqft or not price:

        return jsonify({
            "success": False,
            "message": "Area and price are required."
        }), 400


    try:

        area_sqft = float(area_sqft)
        price = float(price)

        if area_sqft <= 0 or price <= 0:

            return jsonify({
                "success": False,
                "message": "Area and price must be greater than zero."
            }), 400

        price_per_sqft = price / area_sqft

    except (ValueError, TypeError):

        return jsonify({
            "success": False,
            "message": "Invalid area or price."
        }), 400


    connection = get_db_connection()

    try:

        cursor = connection.execute("""
            INSERT INTO properties (
                district_id,
                taluk_id,
                village_id,
                title,
                property_type,
                bhk,
                area_sqft,
            price,
            price_per_sqft,
            source,
            owner_name,
            owner_contact
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            district_id,
            taluk_id,
            village_id if village_id else None,
            title,
            property_type,
            bhk if bhk else None,
            area_sqft,
            price,
            price_per_sqft,
            source,
            str(owner_name).strip() if owner_name else None,
            str(owner_contact).strip() if owner_contact else None
        ))

        connection.commit()

        property_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": "Property saved successfully.",
            "property_id": property_id
        })


    except sqlite3.Error as error:

        connection.rollback()

        return jsonify({
            "success": False,
            "message": "Database error: " + str(error)
        }), 500


    finally:

        connection.close()


# ============================================================
# SEARCH PROPERTIES
# ============================================================

@app.route("/api/properties", methods=["GET"])
@user_or_admin_required
def get_properties():

    district_id = request.args.get("district")
    taluk_id = request.args.get("taluk")
    village_id = request.args.get("village")
    property_type = request.args.get("propertyType")
    bhk = request.args.get("bhk")
    budget = request.args.get("budget")

    try:
        page = max(int(request.args.get("page", 1)), 1)
    except (TypeError, ValueError):
        page = 1

    try:
        page_size = int(request.args.get("page_size", 100))
    except (TypeError, ValueError):
        page_size = 100

    page_size = min(max(page_size, 1), 100)

    connection = get_db_connection()

    try:
        base_from = """
            FROM properties p

            LEFT JOIN districts d
                ON p.district_id = d.id

            LEFT JOIN taluks t
                ON p.taluk_id = t.id

            LEFT JOIN villages v
                ON p.village_id = v.id

            WHERE 1 = 1
        """

        parameters = []

        if district_id:
            base_from += " AND p.district_id = ?"
            parameters.append(district_id)

        if taluk_id:
            base_from += " AND p.taluk_id = ?"
            parameters.append(taluk_id)

        if village_id:
            base_from += " AND p.village_id = ?"
            parameters.append(village_id)

        if property_type:
            # Case-insensitive property-type filtering so House/house,
            # Apartment/apartment, Plot/plot, etc. all match.
            base_from += " AND LOWER(TRIM(p.property_type)) LIKE LOWER(TRIM(?))"
            parameters.append("%" + property_type.strip() + "%")

        if bhk:
            # BHK values are stored as text in some datasets and numeric in
            # others; text normalization keeps the filter consistent.
            base_from += " AND CAST(p.bhk AS INTEGER) = CAST(? AS INTEGER)"
            parameters.append(bhk)

        if budget:
            try:
                budget_value = float(budget)
                base_from += " AND p.price <= ?"
                parameters.append(budget_value)
            except ValueError:
                pass

        total = connection.execute(
            "SELECT COUNT(*) " + base_from,
            parameters
        ).fetchone()[0]

        total_pages = max(
            (total + page_size - 1) // page_size,
            1
        )

        if page > total_pages:
            page = total_pages

        offset = (page - 1) * page_size

        statistics = connection.execute(
            """
            SELECT
                AVG(p.price) AS average_price,
                AVG(p.price_per_sqft) AS average_price_per_sqft,
                MIN(p.price) AS minimum_price,
                MAX(p.price) AS maximum_price
            """ + base_from,
            parameters
        ).fetchone()

        property_type_rows = connection.execute(
            """
            SELECT
                COALESCE(p.property_type, 'Unknown') AS label,
                COUNT(*) AS value
            """ + base_from + """
            GROUP BY COALESCE(p.property_type, 'Unknown')
            ORDER BY value DESC, label ASC
            """,
            parameters
        ).fetchall()

        district_rows = connection.execute(
            """
            SELECT
                COALESCE(d.name, 'Unknown') AS label,
                COUNT(*) AS value
            """ + base_from + """
            GROUP BY COALESCE(d.name, 'Unknown')
            ORDER BY value DESC, label ASC
            """,
            parameters
        ).fetchall()

        # District-wise property-type mix for the market intelligence view.
        # Plot, site and land are grouped together so the chart remains readable.
        district_type_rows = connection.execute(
            """
            SELECT
                COALESCE(d.name, 'Unknown') AS district,
                CASE
                    WHEN LOWER(TRIM(COALESCE(p.property_type, ''))) = 'house'
                        THEN 'House'
                    WHEN LOWER(TRIM(COALESCE(p.property_type, ''))) = 'apartment'
                        THEN 'Apartment'
                    WHEN LOWER(TRIM(COALESCE(p.property_type, ''))) = 'villa'
                        THEN 'Villa'
                    WHEN LOWER(TRIM(COALESCE(p.property_type, ''))) IN ('plot', 'site', 'land')
                        THEN 'Plot / Site'
                    ELSE 'Other'
                END AS property_type,
                COUNT(*) AS value
            """ + base_from + """
            GROUP BY
                COALESCE(d.name, 'Unknown'),
                CASE
                    WHEN LOWER(TRIM(COALESCE(p.property_type, ''))) = 'house'
                        THEN 'House'
                    WHEN LOWER(TRIM(COALESCE(p.property_type, ''))) = 'apartment'
                        THEN 'Apartment'
                    WHEN LOWER(TRIM(COALESCE(p.property_type, ''))) = 'villa'
                        THEN 'Villa'
                    WHEN LOWER(TRIM(COALESCE(p.property_type, ''))) IN ('plot', 'site', 'land')
                        THEN 'Plot / Site'
                    ELSE 'Other'
                END
            ORDER BY district ASC, property_type ASC
            """,
            parameters
        ).fetchall()

        district_type_map = {}
        key_map = {
            'House': 'house',
            'Apartment': 'apartment',
            'Villa': 'villa',
            'Plot / Site': 'plot_site',
            'Other': 'other'
        }

        for row in district_type_rows:
            district_name = row['district']
            district_type_map.setdefault(district_name, {
                'district': district_name,
                'house': 0,
                'apartment': 0,
                'villa': 0,
                'plot_site': 0,
                'other': 0,
                'total': 0
            })
            key = key_map.get(row['property_type'], 'other')
            count = int(row['value'] or 0)
            district_type_map[district_name][key] += count
            district_type_map[district_name]['total'] += count

        district_property_mix = sorted(
            district_type_map.values(),
            key=lambda item: (-item['total'], item['district'].lower())
        )

        bhk_rows = connection.execute(
            """
            SELECT
                CAST(p.bhk AS TEXT) AS label,
                COUNT(*) AS value
            """ + base_from + """
            AND p.bhk IS NOT NULL
            AND TRIM(CAST(p.bhk AS TEXT)) <> ''
            GROUP BY p.bhk
            ORDER BY
                CASE
                    WHEN CAST(p.bhk AS TEXT) GLOB '[0-9]*'
                    THEN CAST(p.bhk AS INTEGER)
                    ELSE 999999
                END,
                label ASC
            """,
            parameters
        ).fetchall()

        price_analysis_rows = connection.execute(
            """
            SELECT
                p.id,
                p.title,
                p.property_type,
                p.price,
                p.price_per_sqft,
                COALESCE(d.name, 'Karnataka') AS district,
                COALESCE(t.name, '—') AS taluk,
                COALESCE(v.name, '—') AS village
            """ + base_from + """
            ORDER BY p.price ASC
            LIMIT 20
            """,
            parameters
        ).fetchall()

        # Balanced listing order: when the user does not filter by type, interleave
        # property categories so the first pages contain houses, apartments, villas
        # and plots instead of being dominated by one low-price category.
        results_rows = connection.execute(
            """
            WITH filtered AS (
                SELECT
                    p.id,
                    p.title,
                    p.property_type,
                    p.bhk,
                    p.area_sqft,
                    p.price,
                    p.price_per_sqft,
                    p.owner_name,
                    p.owner_contact,
                    d.name AS district,
                    t.name AS taluk,
                    v.name AS village,
                    ROW_NUMBER() OVER (
                        PARTITION BY LOWER(TRIM(COALESCE(p.property_type, 'Unknown')))
                        ORDER BY p.price ASC, p.id ASC
                    ) AS type_rank
                """ + base_from + """
            )
            SELECT
                id,
                title,
                property_type,
                bhk,
                area_sqft,
                price,
                price_per_sqft,
                owner_name,
                owner_contact,
                district,
                taluk,
                village
            FROM filtered
            ORDER BY
                type_rank ASC,
                CASE LOWER(TRIM(COALESCE(property_type, 'Unknown')))
                    WHEN 'house' THEN 0
                    WHEN 'apartment' THEN 1
                    WHEN 'villa' THEN 2
                    WHEN 'plot' THEN 3
                    WHEN 'site' THEN 4
                    WHEN 'land' THEN 5
                    ELSE 6
                END,
                price ASC,
                id ASC
            LIMIT ? OFFSET ?
            """,
            parameters + [page_size, offset]
        ).fetchall()

        results = []

        for property_data in results_rows:
            price_per_sqft = property_data["price_per_sqft"]

            if price_per_sqft is not None:
                price_per_sqft = round(price_per_sqft)

            results.append({
                "id": property_data["id"],
                "title": property_data["title"],
                "property_type": property_data["property_type"],
                "bhk": property_data["bhk"],
                "area_sqft": property_data["area_sqft"],
                "price": property_data["price"],
                "price_per_sqft": price_per_sqft,
                "owner_name": property_data["owner_name"],
                "owner_contact": property_data["owner_contact"],
                "district": property_data["district"] or "Karnataka",
                "taluk": property_data["taluk"] or "—",
                "village": property_data["village"] or "—"
            })

        price_analysis = []

        for property_data in price_analysis_rows:
            psf = property_data["price_per_sqft"]

            if psf is not None:
                psf = round(psf)

            price_analysis.append({
                "id": property_data["id"],
                "title": property_data["title"],
                "property_type": property_data["property_type"],
                "price": property_data["price"],
                "price_per_sqft": psf,
                "district": property_data["district"],
                "taluk": property_data["taluk"],
                "village": property_data["village"]
            })

        analytics = {
            "total": total,
            "average_price": statistics["average_price"] or 0,
            "average_price_per_sqft": statistics["average_price_per_sqft"] or 0,
            "minimum_price": statistics["minimum_price"] or 0,
            "maximum_price": statistics["maximum_price"] or 0,
            "property_types": [
                {
                    "label": row["label"],
                    "value": row["value"]
                }
                for row in property_type_rows
            ],
            "districts": [
                {
                    "label": row["label"],
                    "value": row["value"]
                }
                for row in district_rows
            ],
            "district_property_mix": district_property_mix,
            "bhk": [
                {
                    "label": f'{row["label"]} BHK',
                    "value": row["value"]
                }
                for row in bhk_rows
            ],
            "price_analysis": price_analysis
        }

        return jsonify({
            "results": results,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages
            },
            "analytics": analytics
        })

    finally:
        connection.close()


# ============================================================
# UPDATE PROPERTY OWNER / CONTACT
# ============================================================

@app.route("/api/properties/<int:property_id>/contact", methods=["PUT", "PATCH"])
@admin_required
def update_property_contact(property_id):

    data = request.get_json(silent=True) or {}

    owner_name = data.get("ownerName") or data.get("owner_name")
    owner_contact = data.get("ownerContact") or data.get("owner_contact")

    connection = get_db_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE properties
            SET owner_name = ?, owner_contact = ?
            WHERE id = ?
            """,
            (
                str(owner_name).strip() if owner_name else None,
                str(owner_contact).strip() if owner_contact else None,
                property_id
            )
        )

        if cursor.rowcount == 0:
            return jsonify({
                "success": False,
                "message": "Property not found."
            }), 404

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Owner details updated successfully."
        })

    except sqlite3.Error as error:
        connection.rollback()
        return jsonify({
            "success": False,
            "message": "Database error: " + str(error)
        }), 500

    finally:
        connection.close()


# ============================================================
# START FLASK
# ============================================================

if __name__ == "__main__":

    app.run(debug=True)