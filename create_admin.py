from app import app
from models import db
from models.admin import Admin


with app.app_context():

    db.create_all()

    admin = Admin.query.filter_by(
        username="admin"
    ).first()

    if admin is None:

        admin = Admin(
            username="admin"
        )

        admin.set_password(
            "admin123"
        )

        db.session.add(admin)

        db.session.commit()

        print("Admin created successfully!")

    else:

        print("Admin already exists.")