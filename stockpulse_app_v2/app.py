from flask import Flask, send_from_directory

from config import SECRET_KEY
from db import init_db

from routes.auth import auth_bp
from routes.products import products_bp
from routes.sales import sales_bp
from routes.restocks import restocks_bp
from routes.inventory import inventory_bp
from routes.dashboard import dashboard_bp
from routes.reports import reports_bp

app = Flask(__name__, static_folder="static", static_url_path="")
app.secret_key = SECRET_KEY

init_db()  # Initialize the database connection

app.register_blueprint(auth_bp)
app.register_blueprint(products_bp)
app.register_blueprint(sales_bp)
app.register_blueprint(restocks_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(reports_bp)


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
