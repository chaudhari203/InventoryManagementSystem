from models import db

class Supplier(db.Model):

    __tablename__ = "suppliers"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    phone = db.Column(
        db.String(20)
    )

    email = db.Column(
        db.String(100)
    )

    address = db.Column(
        db.Text
    )