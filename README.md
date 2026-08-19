# 📦 Inventory Management System

A professional and responsive **Inventory Management System** built with **Python, Flask, Flask-SQLAlchemy, SQLite, Flask-Login, and Bootstrap 5**.

The system allows an administrator to manage products, categories, suppliers, stock transactions, inventory reports, and dashboard analytics from a centralized interface.

---

## 📌 Project Overview

The Inventory Management System is designed to simplify inventory operations for small and medium-sized businesses.

The application provides:

- 🔐 Admin authentication
- 📊 Inventory dashboard
- 📦 Product management
- 🗂️ Category management
- 🚚 Supplier management
- 📥 Stock In management
- 📤 Stock Out management
- 📋 Transaction history
- 🔎 Product and transaction search
- ⚠️ Low-stock monitoring
- 📈 Inventory reports
- 📊 Stock movement charts
- 💰 Inventory valuation
- 📱 Responsive Bootstrap UI

---

# 🚀 Features

## 🔐 1. Admin Authentication

The system includes secure administrator authentication.

### Features

- Admin login
- Logout
- Protected routes
- Password hashing
- Session management
- Unauthorized users are redirected to login

Authentication is implemented using:

- Flask-Login
- Werkzeug password hashing

---
# 🔐 Demo Login Credentials

For testing the application locally, use the following administrator credentials:

| Field | Value |
|---|---|
| Username | `admin` |
| Password | `admin123` |

### Login URL

```text
http://127.0.0.1:5000/login
# 📊 2. Dashboard

The dashboard provides an overview of the inventory system.

### Dashboard Statistics

- Total Products
- Total Stock
- Total Categories
- Total Suppliers
- Stock In
- Stock Out

### Dashboard Sections

#### Low Stock Products

Displays products whose quantity is below or equal to their configured low-stock threshold.

#### Recent Transactions

Displays the latest stock transactions.

#### Stock Movement Chart

A Chart.js bar chart displays:

- Stock In
- Stock Out

#### Stock Summary

Provides a quick summary of stock movement.

---

# 📦 3. Product Management

The product management module allows administrators to manage inventory products.

### Features

- View products
- Add product
- Edit product
- Delete product
- Search products
- Search by product name
- Search by SKU
- Assign category
- Assign supplier
- Set product price
- Set product quantity
- Configure low-stock threshold

### Product Fields

| Field | Description |
|---|---|
| ID | Unique product ID |
| Name | Product name |
| SKU | Unique stock keeping unit |
| Price | Product price |
| Quantity | Current stock quantity |
| Low Stock Threshold | Minimum stock level |
| Category | Product category |
| Supplier | Product supplier |

---

# 🗂️ 4. Category Management

The category module allows administrators to organize products into categories.

### Features

- View categories
- Add category
- Edit category
- Delete category
- Prevent deletion of categories currently used by products

### Example Categories

- Electronics
- Stationery
- Hardware
- Office Supplies
- Accessories

---

# 🚚 5. Supplier Management

The supplier module manages supplier information.

### Features

- View suppliers
- Add supplier
- Edit supplier
- Delete supplier
- Supplier validation
- Prevent deletion of suppliers currently assigned to products

### Supplier Fields

| Field | Description |
|---|---|
| ID | Unique supplier ID |
| Name | Supplier name |
| Phone | Supplier contact number |
| Email | Supplier email |
| Address | Supplier address |

---

# 📥 6. Stock In

Stock In is used when new inventory is received.

### Process

1. Select product
2. Select `Stock In`
3. Enter quantity
4. Submit transaction
5. Product quantity increases
6. Transaction is recorded

