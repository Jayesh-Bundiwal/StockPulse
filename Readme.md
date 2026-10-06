# StockPulse App v2 📦📊

**StockPulse App v2** is a modular, lightweight inventory, product tracking, and sales management application powered by a Flask Python backend and served with an interactive web user interface.

---

## 🌟 Key Features

- **🔐 Authentication & User Management:** Secure login, token/session management, and role-based helper utilities (`routes/auth.py`, `auth_helpers.py`).
- **📈 Real-Time Dashboard:** Overview of stock levels, recent transactions, sales summaries, and critical metrics (`routes/dashboard.py`).
- **📦 Inventory & Product Tracking:**
  - Track product catalogs, category allocations, pricing, and quantities (`routes/products.py`).
  - Update and adjust stock quantities seamlessly (`routes/inventory.py`).
- **🚚 Restocks & Replenishment:** Log supplier orders, track incoming restocks, and auto-update inventory (`routes/restocks.py`).
- **💳 Sales Logging:** Process sales, record transactions, and auto-deduct stock levels (`routes/sales.py`).
- **📊 Reporting & Analytics:** Generate detailed periodic inventory movement and revenue reports (`routes/reports.py`).

---

## 📁 Directory Structure

```text
stockpulse_app_v2/
├── app.py                 # Main Flask application entry point
├── config.py              # Application configurations & settings
├── db.py                  # Database connection & query helper routines
├── auth_helpers.py        # Authentication & session utilities
├── requirements.txt       # Python dependencies
├── routes/                # Blueprint routes for API endpoints
│   ├── __init__.py
│   ├── auth.py            # Authentication routes
│   ├── dashboard.py       # Metrics & analytics endpoints
│   ├── inventory.py       # Inventory management routes
│   ├── products.py        # CRUD for products
│   ├── reports.py          # Report generation endpoints
│   ├── restocks.py       # Stock replenishment endpoints
│   └── sales.py          # Sales transaction handling
└── static/                # Single Page Application / Static Assets
    └── index.html         # Web frontend GUI
```

---

## ⚙️ Prerequisites

- **Python:** 3.10+ (Python 3.13 tested)
- **Database:** SQLite or PostgreSQL (configured in `config.py` / `db.py`)

---

## 🚀 Getting Started

### 1. Clone the Repository & Navigate to the Project

```bash
cd stockpulse_app_v2
```

### 2. Create and Activate a Virtual Environment

- **On macOS/Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/bin/activate
  ```

- **On Windows:**
  ```bash
  python -m venv venv
  venv\Scripts\activate
  ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configuration

Check `config.py` to set environment variables or database parameters (e.g., database URI, secret keys).

### 5. Run the Application

```bash
python app.py
```

The app will launch locally on `http://127.0.0.1:5000` (or the host/port specified in `app.py`). Open this URL in your web browser to access the frontend application.

---

## 🔗 API Route Blueprint Summary

| Route Module | Prefix / Focus | Description |
| :--- | :--- | :--- |
| `auth.py` | `/api/auth` | User authentication, registration, session management |
| `dashboard.py` | `/api/dashboard` | Aggregated statistics, high-level metrics, summary charts |
| `products.py` | `/api/products` | Create, read, update, delete product catalog entries |
| `inventory.py` | `/api/inventory` | Stock adjustments and current level queries |
| `sales.py` | `/api/sales` | Record new sales and query transaction history |
| `restocks.py` | `/api/restocks` | Log restock batches and update stock counts |
| `reports.py` | `/api/reports` | Exportable data reports and movement logs |

---

## 🛠️ Development & Testing

- To run in debug mode, set `FLASK_DEBUG=1` in your environment or set `debug=True` inside `app.py`.
- Ensure all byte-compiled files (`__pycache__/`) are ignored when committing changes by setting up a standard `.gitignore`.