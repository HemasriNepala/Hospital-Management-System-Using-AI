"""Create first admin user. Run from project folder: python create_admin.py"""
import os
from app import create_app
from extensions import db
from models import User

def main():
    app = create_app()
    with app.app_context():
        if User.query.filter_by(role='admin').first():
            print('Admin user already exists.')
            return
        email = os.environ.get('ADMIN_EMAIL', 'admin@hospital.com')
        password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        admin = User(email=email, role='admin')
        admin.password = password
        admin.is_verified = True
        db.session.add(admin)
        db.session.commit()
        print(f'Admin created: {email} / (your password)')
        print('Change password after first login.')

if __name__ == '__main__':
    main()
