import os

# MySQL connection settings.
# Override any of these with environment variables if your MySQL setup differs,
# e.g. on Windows cmd:  set DB_PASSWORD=yourpassword
#      on Mac/Linux:    export DB_PASSWORD=yourpassword
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "3307")),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", "root"),
    "database": os.environ.get("DB_NAME", "stockpulse"),
}

SECRET_KEY = os.environ.get("SECRET_KEY", "stockpulse-dev-secret-change-me")
