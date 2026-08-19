from models import db


class Product(db.Model):

    __tablename__ = "products"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    sku = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    price = db.Column(
        db.Float,
        nullable=False
    )

    quantity = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    low_stock_threshold = db.Column(
        db.Integer,
        default=5,
        nullable=False
    )

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id"),
        nullable=False
    )

    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey("suppliers.id"),
        nullable=False
    )

    category = db.relationship(
        "Category",
        backref="products"
    )

    supplier = db.relationship(
        "Supplier",
        backref="products"
    )

    transactions = db.relationship(
        "StockTransaction",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Product {self.name}>"