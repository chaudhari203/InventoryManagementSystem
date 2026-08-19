from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    Response,
    send_file
)

from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)
import csv
import io
import os
from sqlalchemy import func, or_

from models import db
from models.admin import Admin
from models.category import Category
from models.supplier import Supplier
from models.product import Product
from models.stock_transaction import StockTransaction
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
app = Flask(__name__)


# ==========================================
# Configuration
# ==========================================

app.config["SECRET_KEY"] = "inventory-management-secret"


database_url = os.environ.get("DATABASE_URL")

if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///inventory.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# ==========================================
# Initialize Database
# ==========================================

db.init_app(app)


# ==========================================
# Flask Login
# ==========================================

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"

login_manager.login_message = "Please login to access this page."

login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):

    return Admin.query.get(int(user_id))


# ==========================================
# Create Database Tables
# ==========================================

with app.app_context():

    db.create_all()

    print("Database tables created successfully!")


# ==========================================
# Login
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        admin = Admin.query.filter_by(
            username=username
        ).first()

        if admin and admin.check_password(password):

            login_user(admin)

            flash(
                "Login successful!",
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid username or password.",
            "danger"
        )

    return render_template(
        "login.html"
    )


# ==========================================
# Logout
# ==========================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "You have been logged out successfully.",
        "success"
    )

    return redirect(
        url_for("login")
    )


# ==========================================
# Dashboard
# ==========================================


@app.route("/")
@login_required
def dashboard():

    total_products = Product.query.count()

    total_categories = Category.query.count()

    total_suppliers = Supplier.query.count()

    total_stock = (
        db.session.query(
            func.coalesce(
                func.sum(Product.quantity),
                0
            )
        ).scalar()
    )

    low_stock_products = (
        Product.query
        .filter(
            Product.quantity <= Product.low_stock_threshold
        )
        .order_by(
            Product.quantity.asc()
        )
        .limit(5)
        .all()
    )

    recent_transactions = (
        StockTransaction.query
        .order_by(
            StockTransaction.id.desc()
        )
        .limit(5)
        .all()
    )

    stock_in = (
        db.session.query(
            func.coalesce(
                func.sum(StockTransaction.quantity),
                0
            )
        )
        .filter(
            StockTransaction.transaction_type == "IN"
        )
        .scalar()
    )

    stock_out = (
        db.session.query(
            func.coalesce(
                func.sum(StockTransaction.quantity),
                0
            )
        )
        .filter(
            StockTransaction.transaction_type == "OUT"
        )
        .scalar()
    )

    return render_template(
        "dashboard.html",

        total_products=total_products,

        total_categories=total_categories,

        total_suppliers=total_suppliers,

        total_stock=total_stock,

        low_stock_products=low_stock_products,

        recent_transactions=recent_transactions,

        stock_in=stock_in,

        stock_out=stock_out
    )
# ==========================================
# PRODUCT MANAGEMENT
# ==========================================


# ------------------------------------------
# View Products
# ------------------------------------------

@app.route("/products")
@login_required
def products():

    keyword = request.args.get(
        "keyword",
        ""
    ).strip()

    page = request.args.get(
        "page",
        1,
        type=int
    )

    query = Product.query

    if keyword:

        query = query.filter(
            or_(
                Product.name.ilike(
                    f"%{keyword}%"
                ),
                Product.sku.ilike(
                    f"%{keyword}%"
                )
            )
        )

    products = (
        query
        .order_by(Product.id.desc())
        .paginate(
            page=page,
            per_page=10,
            error_out=False
        )
    )

    return render_template(
        "products.html",
        products=products,
        keyword=keyword
    )
# ------------------------------------------
# Add Product
# ------------------------------------------

@app.route("/products/add", methods=["GET", "POST"])
@login_required
def add_product():

    categories = Category.query.order_by(
        Category.name
    ).all()

    suppliers = Supplier.query.order_by(
        Supplier.name
    ).all()

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        sku = request.form.get("sku", "").strip()
        price = request.form.get("price", "").strip()
        quantity = request.form.get("quantity", "").strip()
        low_stock_threshold = request.form.get(
            "low_stock_threshold",
            ""
        ).strip()
        category_id = request.form.get("category_id", "").strip()
        supplier_id = request.form.get("supplier_id", "").strip()

        # =========================
        # REQUIRED FIELD VALIDATION
        # =========================

        if not name:
            flash(
                "Product name is required.",
                "danger"
            )
            return redirect(url_for("add_product"))

        if not sku:
            flash(
                "SKU is required.",
                "danger"
            )
            return redirect(url_for("add_product"))

        if not price:
            flash(
                "Price is required.",
                "danger"
            )
            return redirect(url_for("add_product"))

        if not quantity:
            flash(
                "Quantity is required.",
                "danger"
            )
            return redirect(url_for("add_product"))

        if not low_stock_threshold:
            flash(
                "Low stock threshold is required.",
                "danger"
            )
            return redirect(url_for("add_product"))

        if not category_id:
            flash(
                "Please select a category.",
                "danger"
            )
            return redirect(url_for("add_product"))

        if not supplier_id:
            flash(
                "Please select a supplier.",
                "danger"
            )
            return redirect(url_for("add_product"))

        # =========================
        # DUPLICATE SKU
        # =========================

        existing_product = Product.query.filter_by(
            sku=sku
        ).first()

        if existing_product:

            flash(
                "SKU already exists. Please use a different SKU.",
                "danger"
            )

            return redirect(
                url_for("add_product")
            )

        # =========================
        # DATA TYPE VALIDATION
        # =========================

        try:

            price = float(price)
            quantity = int(quantity)
            low_stock_threshold = int(
                low_stock_threshold
            )
            category_id = int(category_id)
            supplier_id = int(supplier_id)

        except ValueError:

            flash(
                "Please enter valid numeric values.",
                "danger"
            )

            return redirect(
                url_for("add_product")
            )

        # =========================
        # VALUE VALIDATION
        # =========================

        if price < 0:

            flash(
                "Price cannot be negative.",
                "danger"
            )

            return redirect(
                url_for("add_product")
            )

        if quantity < 0:

            flash(
                "Quantity cannot be negative.",
                "danger"
            )

            return redirect(
                url_for("add_product")
            )

        if low_stock_threshold < 0:

            flash(
                "Low stock threshold cannot be negative.",
                "danger"
            )

            return redirect(
                url_for("add_product")
            )

        # =========================
        # CHECK CATEGORY
        # =========================

        category = Category.query.get(
            category_id
        )

        if not category:

            flash(
                "Selected category does not exist.",
                "danger"
            )

            return redirect(
                url_for("add_product")
            )

        # =========================
        # CHECK SUPPLIER
        # =========================

        supplier = Supplier.query.get(
            supplier_id
        )

        if not supplier:

            flash(
                "Selected supplier does not exist.",
                "danger"
            )

            return redirect(
                url_for("add_product")
            )

        # =========================
        # CREATE PRODUCT
        # =========================

        product = Product(
            name=name,
            sku=sku,
            price=price,
            quantity=quantity,
            low_stock_threshold=low_stock_threshold,
            category_id=category_id,
            supplier_id=supplier_id
        )

        try:

            db.session.add(product)

            db.session.commit()

            flash(
                "Product added successfully!",
                "success"
            )

            return redirect(
                url_for("products")
            )

        except Exception:

            db.session.rollback()

            flash(
                "Something went wrong while adding the product.",
                "danger"
            )

            return redirect(
                url_for("add_product")
            )

    return render_template(
        "add_product.html",
        categories=categories,
        suppliers=suppliers
    )
@app.route(
    "/products/edit/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def edit_product(id):

    product = Product.query.get_or_404(id)

    categories = Category.query.order_by(
        Category.name
    ).all()

    suppliers = Supplier.query.order_by(
        Supplier.name
    ).all()

    if request.method == "POST":

        product.name = request.form.get(
            "name"
        )

        product.sku = request.form.get(
            "sku"
        )

        product.price = float(
            request.form.get("price")
        )

        product.quantity = int(
            request.form.get("quantity")
        )

        product.low_stock_threshold = int(
            request.form.get(
                "low_stock_threshold"
            )
        )

        product.category_id = int(
            request.form.get(
                "category_id"
            )
        )

        product.supplier_id = int(
            request.form.get(
                "supplier_id"
            )
        )

        db.session.commit()

        flash(
            "Product updated successfully!",
            "success"
        )

        return redirect(
            url_for("products")
        )

    return render_template(
        "edit_product.html",
        product=product,
        categories=categories,
        suppliers=suppliers
    )


@app.route(
    "/products/delete/<int:id>",
    methods=["POST"]
)
@login_required
def delete_product(id):

    product = Product.query.get_or_404(id)

    db.session.delete(product)

    db.session.commit()

    flash(
        "Product deleted successfully!",
        "success"
    )

    return redirect(
        url_for("products")
    )


@app.route(
    "/products/stock-in/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def stock_in(id):

    product = Product.query.get_or_404(id)

    if request.method == "POST":

        quantity = int(
            request.form["quantity"]
        )

        product.quantity += quantity

        transaction = StockTransaction(
            product_id=product.id,
            transaction_type="IN",
            quantity=quantity
        )

        db.session.add(transaction)

        db.session.commit()

        flash(
            "Stock added successfully!",
            "success"
        )

        return redirect(
            url_for("products")
        )

    return render_template(
        "stock_in.html",
        product=product
    )


@app.route(
    "/products/stock-out/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def stock_out(id):

    product = Product.query.get_or_404(id)

    if request.method == "POST":

        quantity = int(
            request.form["quantity"]
        )

        if quantity > product.quantity:

            flash(
                "Not enough stock available.",
                "danger"
            )

            return redirect(
                url_for(
                    "stock_out",
                    id=id
                )
            )

        product.quantity -= quantity

        transaction = StockTransaction(
            product_id=product.id,
            transaction_type="OUT",
            quantity=quantity
        )

        db.session.add(transaction)

        db.session.commit()

        flash(
            "Stock removed successfully!",
            "success"
        )

        return redirect(
            url_for("products")
        )

    return render_template(
        "stock_out.html",
        product=product
    )
@app.route("/categories")
@login_required
def categories():

    categories = Category.query.order_by(
        Category.id.desc()
    ).all()

    return render_template(
        "categories.html",
        categories=categories
    )


@app.route("/categories/add", methods=["GET", "POST"])
@login_required
def add_category():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        if not name:
            flash(
                "Category name is required.",
                "danger"
            )
            return redirect(
                url_for("add_category")
            )

        category = Category(
            name=name
        )

        db.session.add(category)
        db.session.commit()

        flash(
            "Category added successfully!",
            "success"
        )

        return redirect(
            url_for("categories")
        )

    return render_template(
        "add_category.html"
    )

@app.route("/categories/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_category(id):

    category = Category.query.get_or_404(id)

    if request.method == "POST":

        category.name = request.form["name"]

        db.session.commit()

        flash("Category updated successfully!", "success")

        return redirect(url_for("categories"))

    return render_template(
        "edit_category.html",
        category=category
    )


@app.route("/categories/delete/<int:id>", methods=["POST"])
@login_required
def delete_category(id):

    category = Category.query.get_or_404(id)

    # Check if category is being used by any products
    if category.products:

        flash(
            f"Cannot delete '{category.name}' because "
            f"{len(category.products)} product(s) are using this category.",
            "danger"
        )

        return redirect(url_for("categories"))

    db.session.delete(category)
    db.session.commit()

    flash(
        f"Category '{category.name}' deleted successfully!",
        "success"
    )

    return redirect(url_for("categories"))
# ==========================================
# SUPPLIER MANAGEMENT
# ==========================================

@app.route("/suppliers")
@login_required
def suppliers():

    suppliers = (
        Supplier.query
        .order_by(Supplier.id.desc())
        .all()
    )

    return render_template(
        "suppliers.html",
        suppliers=suppliers
    )


@app.route(
    "/suppliers/add",
    methods=["GET", "POST"]
)
@login_required
def add_supplier():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        if not name:

            flash(
                "Supplier name is required.",
                "danger"
            )

            return redirect(
                url_for("add_supplier")
            )

        supplier = Supplier(
            name=name,
            phone=phone,
            email=email,
            address=address
        )

        db.session.add(supplier)
        db.session.commit()

        flash(
            "Supplier added successfully!",
            "success"
        )

        return redirect(
            url_for("suppliers")
        )

    return render_template(
        "add_supplier.html"
    )


@app.route("/suppliers/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_supplier(id):

    supplier = Supplier.query.get_or_404(id)

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()

        if not name:
            flash("Supplier name is required.", "danger")

            return render_template(
                "edit_supplier.html",
                supplier=supplier
            )

        supplier.name = name
        supplier.phone = phone
        supplier.email = email

        db.session.commit()

        flash(
            "Supplier updated successfully!",
            "success"
        )

        return redirect(url_for("suppliers"))

    return render_template(
        "edit_supplier.html",
        supplier=supplier
    )


@app.route("/suppliers/delete/<int:id>", methods=["POST"])
@login_required
def delete_supplier(id):

    supplier = Supplier.query.get_or_404(id)

    # Check if supplier is being used by products
    if supplier.products:

        flash(
            f"Cannot delete '{supplier.name}' because "
            f"{len(supplier.products)} product(s) are using this supplier.",
            "danger"
        )

        return redirect(url_for("suppliers"))

    db.session.delete(supplier)

    db.session.commit()

    flash(
        f"Supplier '{supplier.name}' deleted successfully!",
        "success"
    )

    return redirect(url_for("suppliers"))
@app.route(
    "/stock",
    methods=["GET", "POST"]
)
@login_required
def stock():

    products = (
        Product.query
        .order_by(Product.name)
        .all()
    )

    # ==========================
    # UPDATE STOCK
    # ==========================

    if request.method == "POST":

        product_id = int(
            request.form.get("product_id")
        )

        transaction_type = request.form.get(
            "transaction_type"
        )

        quantity = int(
            request.form.get("quantity")
        )

        product = Product.query.get_or_404(
            product_id
        )

        if quantity <= 0:

            flash(
                "Quantity must be greater than 0.",
                "danger"
            )

            return redirect(
                url_for("stock")
            )

        if transaction_type == "IN":

            product.quantity += quantity

        elif transaction_type == "OUT":

            if product.quantity < quantity:

                flash(
                    "Not enough stock available.",
                    "danger"
                )

                return redirect(
                    url_for("stock")
                )

            product.quantity -= quantity

        else:

            flash(
                "Invalid transaction type.",
                "danger"
            )

            return redirect(
                url_for("stock")
            )

        transaction = StockTransaction(
            product_id=product.id,
            transaction_type=transaction_type,
            quantity=quantity
        )

        db.session.add(transaction)

        db.session.commit()

        flash(
            "Stock updated successfully.",
            "success"
        )

        return redirect(
            url_for("stock")
        )

    # ==========================
    # SEARCH & FILTER
    # ==========================

    keyword = request.args.get(
        "keyword",
        ""
    ).strip()

    transaction_type = request.args.get(
        "type",
        ""
    ).strip().upper()

    query = StockTransaction.query.join(
        Product
    )

    # Search product name / SKU

    if keyword:

        query = query.filter(
            or_(
                Product.name.ilike(
                    f"%{keyword}%"
                ),

                Product.sku.ilike(
                    f"%{keyword}%"
                )
            )
        )

    # Filter IN / OUT

    if transaction_type in ["IN", "OUT"]:

        query = query.filter(
            StockTransaction.transaction_type
            == transaction_type
        )

    transactions = (
        query
        .order_by(
            StockTransaction.id.desc()
        )
        .all()
    )

    return render_template(
        "stock.html",

        products=products,

        transactions=transactions,

        keyword=keyword,

        transaction_type=transaction_type
    )

@app.route("/reports")
@login_required
def reports():

    # ==========================================
    # SUMMARY
    # ==========================================

    total_products = Product.query.count()

    total_stock = (
        db.session.query(
            func.coalesce(
                func.sum(Product.quantity),
                0
            )
        ).scalar()
    )

    inventory_value = (
        db.session.query(
            func.coalesce(
                func.sum(
                    Product.price * Product.quantity
                ),
                0
            )
        ).scalar()
    )

    stock_in = (
        db.session.query(
            func.coalesce(
                func.sum(StockTransaction.quantity),
                0
            )
        )
        .filter(
            StockTransaction.transaction_type == "IN"
        )
        .scalar()
    )

    stock_out = (
        db.session.query(
            func.coalesce(
                func.sum(StockTransaction.quantity),
                0
            )
        )
        .filter(
            StockTransaction.transaction_type == "OUT"
        )
        .scalar()
    )


    # ==========================================
    # LOW STOCK PRODUCTS
    # ==========================================

    low_stock_products = (
        Product.query
        .filter(
            Product.quantity <= Product.low_stock_threshold
        )
        .order_by(
            Product.quantity.asc()
        )
        .all()
    )


    # ==========================================
    # TOP STOCK PRODUCTS
    # ==========================================

    top_stock_products = (
        Product.query
        .order_by(
            Product.quantity.desc()
        )
        .limit(10)
        .all()
    )


    # ==========================================
    # STOCK MOVEMENT CHART DATA
    # ==========================================

    stock_chart_labels = [
        "Stock In",
        "Stock Out"
    ]

    stock_chart_data = [
        stock_in,
        stock_out
    ]


    # ==========================================
    # TOP PRODUCTS CHART DATA
    # ==========================================

    product_chart_labels = [
        product.name
        for product in top_stock_products
    ]

    product_chart_data = [
        product.quantity
        for product in top_stock_products
    ]


    # ==========================================
    # RENDER REPORTS
    # ==========================================

    return render_template(
        "reports.html",

        total_products=total_products,

        total_stock=total_stock,

        inventory_value=inventory_value,

        stock_in=stock_in,

        stock_out=stock_out,

        low_stock_products=low_stock_products,

        top_stock_products=top_stock_products,

        stock_chart_labels=stock_chart_labels,

        stock_chart_data=stock_chart_data,

        product_chart_labels=product_chart_labels,

        product_chart_data=product_chart_data
    )

    # ==========================================
# EXPORT PRODUCTS CSV
# ==========================================

@app.route("/reports/export/products")
@login_required
def export_products():

    products = (
        Product.query
        .order_by(Product.id.asc())
        .all()
    )

    output = io.StringIO()

    writer = csv.writer(output)

    # Header
    writer.writerow([
        "ID",
        "Product Name",
        "SKU",
        "Category",
        "Supplier",
        "Price",
        "Quantity",
        "Low Stock Threshold"
    ])

    # Data
    for product in products:

        writer.writerow([
            product.id,
            product.name,
            product.sku,
            product.category.name if product.category else "",
            product.supplier.name if product.supplier else "",
            product.price,
            product.quantity,
            product.low_stock_threshold
        ])

    response = Response(
        output.getvalue(),
        mimetype="text/csv"
    )

    response.headers["Content-Disposition"] = (
        "attachment; filename=inventory_products.csv"
    )

    return response


# ==========================================
# EXPORT TRANSACTIONS CSV
# ==========================================

@app.route("/reports/export/transactions")
@login_required
def export_transactions():

    transactions = (
        StockTransaction.query
        .order_by(
            StockTransaction.id.asc()
        )
        .all()
    )

    output = io.StringIO()

    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Transaction ID",
        "Product",
        "SKU",
        "Transaction Type",
        "Quantity"
    ])

    # Data
    for transaction in transactions:

        writer.writerow([
            transaction.id,
            transaction.product.name
            if transaction.product else "",
            transaction.product.sku
            if transaction.product else "",
            transaction.transaction_type,
            transaction.quantity
        ])

    response = Response(
        output.getvalue(),
        mimetype="text/csv"
    )

    response.headers["Content-Disposition"] = (
        "attachment; filename=stock_transactions.csv"
    )

    return response
@app.route("/reports/pdf")
@login_required
def reports_pdf():

    products = (
        Product.query
        .order_by(Product.name)
        .all()
    )

    total_products = Product.query.count()

    total_stock = (
        db.session.query(
            func.coalesce(
                func.sum(Product.quantity),
                0
            )
        ).scalar()
    )

    stock_in = (
        db.session.query(
            func.coalesce(
                func.sum(StockTransaction.quantity),
                0
            )
        )
        .filter(
            StockTransaction.transaction_type == "IN"
        )
        .scalar()
    )

    stock_out = (
        db.session.query(
            func.coalesce(
                func.sum(StockTransaction.quantity),
                0
            )
        )
        .filter(
            StockTransaction.transaction_type == "OUT"
        )
        .scalar()
    )

    inventory_value = (
        db.session.query(
            func.coalesce(
                func.sum(
                    Product.price * Product.quantity
                ),
                0
            )
        ).scalar()
    )

    # Create PDF in memory
    buffer = BytesIO()

    pdf = canvas.Canvas(
        buffer,
        pagesize=A4
    )

    width, height = A4

    # =========================
    # TITLE
    # =========================

    pdf.setFont(
        "Helvetica-Bold",
        20
    )

    pdf.drawString(
        50,
        height - 50,
        "Inventory Management Report"
    )

    pdf.setFont(
        "Helvetica",
        10
    )

    pdf.drawString(
        50,
        height - 70,
        "Inventory Summary"
    )

    # =========================
    # SUMMARY
    # =========================

    y = height - 110

    pdf.setFont(
        "Helvetica-Bold",
        11
    )

    pdf.drawString(
        50,
        y,
        f"Total Products: {total_products}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Total Stock: {total_stock}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Total Stock In: {stock_in}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Total Stock Out: {stock_out}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Inventory Value: Rs. {inventory_value:.2f}"
    )

    # =========================
    # PRODUCT TABLE
    # =========================

    y -= 40

    pdf.setFont(
        "Helvetica-Bold",
        11
    )

    pdf.drawString(50, y, "Product")
    pdf.drawString(220, y, "SKU")
    pdf.drawString(340, y, "Price")
    pdf.drawString(420, y, "Stock")

    y -= 20

    pdf.setFont(
        "Helvetica",
        9
    )

    for product in products:

        if y < 50:

            pdf.showPage()

            y = height - 50

            pdf.setFont(
                "Helvetica",
                9
            )

        pdf.drawString(
            50,
            y,
            product.name[:25]
        )

        pdf.drawString(
            220,
            y,
            product.sku[:18]
        )

        pdf.drawString(
            340,
            y,
            f"Rs. {product.price:.2f}"
        )

        pdf.drawString(
            420,
            y,
            str(product.quantity)
        )

        y -= 18

    pdf.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="inventory_report.pdf",
        mimetype="application/pdf"
    )
# ==========================================
# Run Application
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=True
    )