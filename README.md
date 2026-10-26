# Wareloom — Smart Warehouse Management System

Wareloom is a Django-based warehouse management web application for managing inventory, customer orders, shipments, and operational visibility from a single interface. The project combines server-rendered Django pages with REST API endpoints for products, orders, and shipments.

> **Project status:** This README documents the features and structure found in the supplied project archive. It does not claim that the application has been deployed or that every feature has been production-tested.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Application Modules](#application-modules)
- [Data Models](#data-models)
- [Project Structure](#project-structure)
- [Local Setup](#local-setup)
- [Environment Variables](#environment-variables)
- [Run the Application](#run-the-application)
- [URL Routes](#url-routes)
- [REST API Endpoints](#rest-api-endpoints)
- [Reports and CSV Exports](#reports-and-csv-exports)
- [Database and Media Files](#database-and-media-files)
- [Deployment Notes](#deployment-notes)
- [Security and Repository Hygiene](#security-and-repository-hygiene)
- [Future Improvements](#future-improvements)

## Overview

Wareloom is designed around a typical warehouse workflow:

**Inventory → Customer Orders → Stock Validation → Shipments → Dashboard and Reports**

The application includes authentication pages, protected operational pages, product and order management, shipment tracking, inventory insights, and downloadable CSV reports. It uses Django models backed by a relational database and Django REST Framework serializers for API representations.

## Features

### 1. Authentication and access to pages
- Login and signup pages.
- Logout route.
- Login-protected dashboard, inventory, order, shipment, analytics, and inventory insight/report pages.
- Django's built-in authentication system.

### 2. Product and inventory management
- Product records include name, SKU, category, quantity, price, supplier, warehouse location, reorder level, expiry date, manufacturing date, description, and optional image.
- Product management page.
- Product REST API endpoints.
- Inventory value and stock-level information used by dashboard/analytics and reports.
- Low-stock and out-of-stock monitoring.

### 3. Customer order management
- Order records include order number/date, customer contact details, shipping address, city, PIN code, product, quantity, unit price, total amount, payment details, shipping method, order status, tracking number, and shipping/delivery dates.
- Supported order statuses: Pending, Processing, Picking, Packed, Shipped, Delivered, and Cancelled.
- Supported payment statuses: Pending, Paid, Failed, and Refunded.
- Supported payment methods: Cash on Delivery, Credit Card, UPI, Net Banking, and Wallet.
- Supported shipping methods: Standard Shipping, Express Shipping, and Overnight Shipping.
- Total amount is calculated from quantity × unit price when an order is saved.
- Order management page and REST API endpoints.

### 4. Shipment management
- Shipment records are linked one-to-one with orders.
- Shipment details include shipment ID, tracking number, carrier, shipment date, and status.
- Supported shipment statuses: Preparing, Shipped, In Transit, Delivered, and Delayed.
- Shipment management page and REST API endpoints.

### 5. Dashboard and analytics
- Dashboard page for warehouse overview.
- Analytics page with inventory/order/shipment summaries and chart-oriented context.
- Inventory value and stock-related indicators.
- Operational counts and status summaries.

### 6. Inventory insight modules
- **Expiry Rescue** — a page focused on inventory expiry-related information.
- **Stock Sense** — a page for stock-level insights.
- **Inventory Time Machine** — a page for historical stock-movement information.
- **Reports & Alerts** — operational alerts and CSV downloads, including stock and order/shipment exceptions.

### 7. Reports and CSV exports
The Reports & Alerts module provides downloadable CSV reports for:
- Inventory
- Orders
- Shipments
- Inventory valuation

It also surfaces operational conditions such as out-of-stock products, low-stock products, overdue orders, and delayed shipments.

### 8. REST API
Django REST Framework serializers are defined for products, orders, and shipments. The order serializer also exposes a read-only product name; the shipment serializer exposes a read-only order number and customer name.

## Technology Stack

- **Language:** Python
- **Web framework:** Django
- **API framework:** Django REST Framework
- **Database in the supplied configuration:** SQLite
- **Frontend:** Django templates, HTML, CSS, and JavaScript
- **Image handling:** Pillow / Django `ImageField`
- **Environment configuration:** `python-dotenv`

The project includes static CSS, JavaScript, and image assets under `backend/static/`.

## Application Modules

| Module | Route | Purpose |
|---|---|---|
| Home | `/` | Landing page |
| Login | `/login/` | User login |
| Signup | `/signup/` | User registration |
| Dashboard | `/dashboard/` | Warehouse overview |
| Products | `/products/` | Product/inventory management |
| Orders | `/orders/` | Customer order management |
| Shipments | `/shipments/` | Shipment management and status |
| Analytics | `/analytics/` | Operational analytics |
| Contact | `/contact/` | Contact page |
| Expiry Rescue | `/expiry-rescue/` | Expiry-related inventory view |
| Stock Sense | `/stock-sense/` | Stock-level insight page |
| Inventory Time Machine | `/inventory-time-machine/` | Stock movement/history view |
| Reports & Alerts | `/reports-alerts/` | Operational alerts and reports |
| Django Admin | `/admin/` | Django administration |

## Data Models

The supplied `backend/core/models.py` defines four main models:

### `products`
Stores product and inventory attributes, including SKU, category, quantity, price, supplier, location, reorder level, expiry/manufacturing dates, description, and an optional uploaded image.

### `StockMovement`
Records stock changes with movement type, previous and new quantity, quantity changed, reason, user (when available), and timestamp. Movement types include Received, Dispatched, Adjustment, and Return.

### `orders`
Stores customer order details, product and quantity, prices, payment information, order status, shipping information, and delivery dates. The model calculates `total_amount` when saved.

### `shipments`
Stores shipment and carrier information and is linked one-to-one to an order.

## Project Structure

The archive supplied for this README contains the following main application files and folders:

```text
Full Stack Develop/
├── backend/
│   ├── core/
│   │   ├── migrations/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── admin.py
│   │   └── tests.py
│   ├── warehouse/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   ├── asgi.py
│   │   └── mongodb.py
│   ├── templates/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── media/                 # Uploaded product media (local)
│   ├── manage.py
│   └── .gitignore
├── requirements.txt
├── projectflow.txt
└── pdf/
```

The supplied archive also contains local database files and a virtual environment. These are development artifacts and should generally not be included in a public source repository or deployment package.

## Local Setup

### Prerequisites
- Python installed on your machine.
- Git (optional, for source control).
- A terminal such as the VS Code integrated terminal.

### 1. Open the project folder

Open the `Full Stack Develop` folder in VS Code. In the terminal, navigate to the `backend` directory:

```powershell
cd backend
```

### 2. Create and activate a virtual environment (recommended)

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use your organization's approved execution-policy approach or activate the environment from Command Prompt instead.

### 3. Install dependencies

The archive contains a `requirements.txt` at the outer project level. From the outer project folder, run:

```powershell
python -m pip install -r requirements.txt
```

If the requirements file cannot be read correctly, recreate it in UTF-8 from the activated environment after installing the dependencies used by the project:

```powershell
python -m pip install Django djangorestframework Pillow python-dotenv
python -m pip freeze > requirements.txt
```

Keep a deployment-ready `requirements.txt` in the directory from which your hosting provider installs dependencies. For a Render service whose root directory is `backend`, place a UTF-8 `backend/requirements.txt` there.

### 4. Configure environment variables

Create `backend/.env` for local development. Do not commit this file. Example:

```env
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

The supplied settings load `.env` with `python-dotenv` and read `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, and `DJANGO_ALLOWED_HOSTS`.

### 5. Apply database migrations

From `backend/`:

```powershell
python manage.py migrate
```

### 6. Create an admin user (optional)

```powershell
python manage.py createsuperuser
```

### 7. Run Django's system check and start the development server

```powershell
python manage.py check
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

## Environment Variables

| Variable | Purpose | Local example |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django cryptographic secret | Generate a private value |
| `DJANGO_DEBUG` | Enables/disables debug mode | `True` locally; `False` in production |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hostnames | `127.0.0.1,localhost` |

The application settings in the supplied archive configure the console email backend. SMTP credentials are not required for that console backend.

## Run the Application

Typical development commands, run from `backend/`:

```powershell
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Only run `makemigrations` after changing model definitions and reviewing the resulting migration files. The project already includes migrations.

## URL Routes

The route list below reflects the URL configuration in `backend/warehouse/urls.py`.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Landing page |
| GET/POST | `/login/` | Login view |
| GET/POST | `/signup/` | Signup view |
| GET | `/logout/` | Logout |
| GET | `/dashboard/` | Dashboard |
| GET/POST | `/products/` | Product management page |
| GET/POST | `/orders/` | Order management page |
| GET | `/shipments/` | Shipment management page |
| GET | `/analytics/` | Analytics page |
| GET | `/contact/` | Contact page |
| GET | `/expiry-rescue/` | Expiry-related insights |
| GET | `/stock-sense/` | Stock insights |
| GET | `/inventory-time-machine/` | Stock history |
| GET | `/reports-alerts/` | Operational reports and alerts |
| GET | `/reports/export/inventory/` | Inventory CSV export |
| GET | `/reports/export/orders/` | Orders CSV export |
| GET | `/reports/export/shipments/` | Shipments CSV export |
| GET | `/reports/export/valuation/` | Inventory valuation CSV export |
| GET | `/admin/` | Django admin |

The product/order/shipment page routes support the page workflows; the exact request methods accepted by each view depend on the implementation in `core/views.py`.

## REST API Endpoints

The URL configuration defines the following API routes:

| Endpoint | Purpose |
|---|---|
| `/api/products/` | Product collection |
| `/api/products/<product_id>/` | Individual product |
| `/api/orders/` | Order collection |
| `/api/orders/<order_id>/` | Individual order |
| `/api/shipments/` | Shipment collection |
| `/api/shipments/<shipment_pk>/` | Individual shipment |

The API views are implemented in `backend/core/views.py`; serializers are in `backend/core/serializers.py`. Consult those files for supported HTTP methods, validation, response formats, and error handling. API authentication and authorization should be reviewed before exposing the endpoints publicly.

## Reports and CSV Exports

The Reports & Alerts page is available at `/reports-alerts/`. CSV export endpoints are:

- `/reports/export/inventory/`
- `/reports/export/orders/`
- `/reports/export/shipments/`
- `/reports/export/valuation/`

The reports are intended to help review current inventory, order/shipment operations, stock exceptions, and inventory valuation.

## Database and Media Files

- The supplied settings use SQLite by default.
- The archive contains `backend/db.sqlite3` and two database backup files. These may contain local development records and should be reviewed before sharing.
- Uploaded product images are stored under `backend/media/products/` by the model's `ImageField` configuration.
- Local SQLite files and uploaded media do not automatically transfer to a cloud deployment.
- For production, use a managed database such as PostgreSQL and durable media/object storage if uploaded images must persist.

## Deployment Notes

This project can be adapted for a Django hosting platform such as Render, but production deployment requires additional configuration and testing.

Before deploying:

1. Ensure `requirements.txt` is UTF-8 encoded and present in the service root directory.
2. Configure a strong `DJANGO_SECRET_KEY` through the host's environment-variable settings.
3. Set `DJANGO_DEBUG=False`.
4. Set `DJANGO_ALLOWED_HOSTS` to the deployed hostname.
5. Configure a persistent production database and migrate the schema.
6. Configure static-file collection and serving (for example, with WhiteNoise).
7. Configure durable media storage for product images.
8. Review CSRF trusted origins, HTTPS/security settings, logging, and database backups.
9. Run `python manage.py check --deploy` and resolve deployment warnings before public release.

A deployment script or Gunicorn command should only be added after the production dependencies and settings have been verified. The supplied archive does not establish that the application is already deployed.

## Security and Repository Hygiene

Before sharing the ZIP file or publishing the repository, check all of the following:

- Do not share `.env` or any file containing secret keys/passwords.
- Do not commit virtual environments (`venv/` or `.venv/`).
- Exclude local SQLite databases and database backups unless you intentionally want to share sanitized demo data.
- Review uploaded media for private information.
- Keep `__pycache__/`, compiled Python files, and generated static output out of source control.
- If a secret was ever committed or included in a shared ZIP, rotate it; deleting it from the latest commit alone does not remove it from previous Git history.
- Ensure the root `.gitignore` or `backend/.gitignore` covers the relevant files. Git ignore rules do not automatically untrack files already committed.

## Future Improvements

Possible next steps (not claims about current implementation):

- Automated tests for product, order, shipment, and reporting workflows.
- Role-based permissions for warehouse staff, managers, and administrators.
- API authentication, throttling, and schema/documentation.
- PostgreSQL migration and durable media storage for deployment.
- Audit logging for important inventory and order changes.
- Automated deployment and continuous integration.
- More comprehensive error handling, monitoring, and backup/restore procedures.

## Author

**Wareloom — Smart Warehouse Management System**

A Django project focused on bringing inventory, orders, shipment tracking, and operational reporting into one warehouse workflow.
