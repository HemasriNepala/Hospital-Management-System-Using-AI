from app import create_app
from extensions import db
from models import User

app = create_app()
with app.app_context():
    users = User.query.all()
    print("Users in database:")
    for user in users:
        print(f"ID: {user.id}, Email: {user.email}, Role: {user.role}, Verified: {user.is_verified}")
