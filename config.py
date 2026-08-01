"""
Central configuration for Maison Elara.
All secrets are read from environment variables (via a .env file locally,
or real environment variables in production). Nothing sensitive is
hard-coded here or sent to the browser.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # reads a local .env file if present


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    DEBUG = os.environ.get("FLASK_DEBUG", "True") == "True"

    DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maison_elara.db")

    # Stripe
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    #STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
    CURRENCY = os.environ.get("CURRENCY", "usd")

    # Cloudinary
    CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET", "")

    STORE_NAME = os.environ.get("STORE_NAME", "Maison Elara")

    MAX_CONTENT_LENGTH = 6 * 1024 * 1024  # 6MB max upload
