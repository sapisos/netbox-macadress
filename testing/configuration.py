"""
NetBox configuration for running the plugin's tests. Not for production use.

Copy it to netbox/netbox/configuration.py in a NetBox checkout, then:
    python manage.py test netbox_macadress.tests
"""

import os

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "netbox"),
        "USER": os.getenv("DB_USER", "netbox"),
        "PASSWORD": os.getenv("DB_PASSWORD", "netbox"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": 300,
    }
}

REDIS = {
    "tasks": {
        "HOST": os.getenv("REDIS_HOST", "localhost"),
        "PORT": int(os.getenv("REDIS_PORT", 6379)),
        "PASSWORD": "",
        "DATABASE": 0,
        "SSL": False,
    },
    "caching": {
        "HOST": os.getenv("REDIS_HOST", "localhost"),
        "PORT": int(os.getenv("REDIS_PORT", 6379)),
        "PASSWORD": "",
        "DATABASE": 1,
        "SSL": False,
    },
}

SECRET_KEY = "test-secret-key-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
API_TOKEN_PEPPERS = {1: "test-pepper-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOP"}

DEBUG = False
# Allows makemigrations, which NetBox otherwise refuses outside development.
DEVELOPER = True

PLUGINS = ["netbox_macadress"]
PLUGINS_CONFIG = {
    "netbox_macadress": {
        "lookup_on_save": False,
    },
}
