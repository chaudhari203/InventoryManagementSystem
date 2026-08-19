
from models import db


class StockTransaction(db.Model):

    __tablename__ = "stock_transactions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    transaction_type = db.Column(
        db.String(10),
        nullable=False
    )

    quantity = db.Column(
        db.Integer,
        nullable=False
    )

    product = db.relationship(
        "Product",
        back_populates="transactions"
    )