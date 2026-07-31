"""
Simple SQLite database helper for Maison Elara.
No ORM — plain sqlite3 with row factory so results behave like dicts.
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash
from config import Config


def get_db():
    """Open a new database connection with rows accessible by column name."""
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(admin_email="admin@maisonelara.com", admin_password="admin123"):
    """
    Create all tables from schema.sql and seed sample data.
    Run this once via: python database.py
    """
    conn = get_db()
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    with open(schema_path, "r") as f:
        conn.executescript(f.read())

    # Create the admin account with a properly hashed password
    conn.execute(
        "INSERT INTO users (name, email, password_hash, is_admin) VALUES (?, ?, ?, 1)",
        ("Admin", admin_email, generate_password_hash(admin_password)),
    )
    conn.commit()
    conn.close()
    print(f"Database initialized at {Config.DATABASE}")
    print(f"Admin login -> email: {admin_email}  password: {admin_password}")
    print("IMPORTANT: change this password after your first login.")


if __name__ == "__main__":
    if os.path.exists(Config.DATABASE):
        confirm = input(
            f"'{Config.DATABASE}' already exists. Re-initializing will ERASE all data. Continue? [y/N] "
        )
        if confirm.lower() != "y":
            print("Cancelled.")
            raise SystemExit(0)
        os.remove(Config.DATABASE)
    init_db()
