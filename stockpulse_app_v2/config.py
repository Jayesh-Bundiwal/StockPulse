import os

# MySQL connection settings.
# Override any of these with environment variables if your MySQL setup differs,
# e.g. on Windows cmd:  set DB_PASSWORD=yourpassword
#      on Mac/Linux:    export DB_PASSWORD=yourpassword
DB_CONFIG = {
    "host": os.environ.get("DB_HOST"),
    "port": int(os.environ.get("DB_PORT")),
    "user": os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASSWORD"),
    "database": os.environ.get("DB_NAME"),
}

SECRET_KEY = os.environ.get("SECRET_KEY", "stockpulse-dev-secret-change-me")
