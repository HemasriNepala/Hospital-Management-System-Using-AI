"""Authentication: login, register, OTP verification."""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, current_user, login_required
from extensions import db
from models import User, PatientProfile, DoctorProfile
from utils import generate_otp, otp_expiry_minutes, send_otp_email

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main_routes.index'))
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        role = request.form.get('role', 'patient')
        if not email or not password:
            flash('Please enter email and password.', 'danger')
            return render_template('auth/login.html')
        user = User.query.filter_by(email=email, role=role).first()
        if not user:
            # Check if user exists with another role
            other_user = User.query.filter_by(email=email).first()
            if other_user:
                flash(f'Record found for {email} but it is registered as a {other_user.role.capitalize()}. Please select the correct role above.', 'warning')
            else:
                flash('Invalid email or password. Please check your credentials.', 'danger')
            return render_template('auth/login.html')
        
        if not user.check_password(password):
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('auth/login.html')
        if not user.is_verified:
            otp = generate_otp(6)
            user.otp = otp
            user.otp_expires = datetime.utcnow() + timedelta(minutes=otp_expiry_minutes())
            db.session.commit()
            send_otp_email(user.email, otp)
            if not current_app.config.get('MAIL_USERNAME'):
                flash(f'Verification code (DEV): {otp}', 'info')
            session['verify_user_id'] = user.id
            return redirect(url_for('auth.verify_otp'))
        login_user(user)
        if user.role == 'admin':
            return redirect(url_for('admin_routes.dashboard'))
        if user.role == 'doctor':
            return redirect(url_for('doctor_routes.dashboard'))
        return redirect(url_for('patient_routes.dashboard'))
    return render_template('auth/login.html')

@bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    user_id = session.get('verify_user_id')
    if not user_id:
        flash('Please login first.', 'warning')
        return redirect(url_for('auth.login'))
    user = User.query.get(user_id)
    if not user:
        session.pop('verify_user_id', None)
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        otp = (request.form.get('otp') or '').strip()
        if not otp:
            flash('Please enter the 6-digit code.', 'danger')
            return render_template('auth/verify_otp.html')
        if user.otp != otp:
            flash('Wrong code. Please check and try again.', 'danger')
            return render_template('auth/verify_otp.html')
        if user.otp_expires and user.otp_expires < datetime.utcnow():
            flash('Code expired. Please login again to get a new code.', 'danger')
            return redirect(url_for('auth.login'))
        user.is_verified = True
        user.otp = None
        user.otp_expires = None
        db.session.commit()
        session.pop('verify_user_id', None)
        login_user(user)
        if user.role == 'admin':
            return redirect(url_for('admin_routes.dashboard'))
        if user.role == 'doctor':
            return redirect(url_for('doctor_routes.dashboard'))
        return redirect(url_for('patient_routes.dashboard'))

    # GET request: Show code in Dev Mode if not using real email
    if not current_app.config.get('MAIL_USERNAME'):
        flash(f'DEV MODE: Your code is {user.otp}', 'info')
    return render_template('auth/verify_otp.html', email=user.email)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main_routes.index'))
    if request.method == 'POST':
        role = request.form.get('role', 'patient')
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        full_name = (request.form.get('full_name') or '').strip()
        phone = (request.form.get('phone') or '').strip()
        if not email or not password or not full_name:
            flash('Please fill in email, password and full name.', 'danger')
            return render_template('auth/register.html')
        if User.query.filter_by(email=email, role=role).first():
            flash(f'An account with this email is already registered as a {role.capitalize()}. Please login instead.', 'warning')
            return render_template('auth/register.html')
            
        user = User(email=email, role=role)
        user.password = password
        # Auto-verify admins to make set-up easier for the user
        user.is_verified = (role == 'admin')
        db.session.add(user)
        db.session.flush()
        if role == 'patient':
            profile = PatientProfile(user_id=user.id)
            profile.full_name = full_name
            profile.phone = phone
            profile.gender = request.form.get('gender')
            profile.date_of_birth = request.form.get('date_of_birth')
            profile.address = request.form.get('address')
            profile.blood_group = request.form.get('blood_group')
            db.session.add(profile)
        elif role == 'doctor':
            profile = DoctorProfile(user_id=user.id)
            profile.full_name = full_name
            profile.phone = phone
            profile.specialization = request.form.get('specialization') or 'General'
            profile.qualification = request.form.get('qualification')
            db.session.add(profile)
        if not user.is_verified:
            otp = generate_otp(6)
            user.otp = otp
            user.otp_expires = datetime.utcnow() + timedelta(minutes=otp_expiry_minutes())
            db.session.commit()
            send_otp_email(user.email, otp)
            if not current_app.config.get('MAIL_USERNAME'):
                flash(f'Verification code (DEV): {otp}', 'info')
            session['verify_user_id'] = user.id
            flash('Account created. Please enter the code sent to your email.', 'success')
            return redirect(url_for('auth.verify_otp'))
        
        # If already verified (Admin)
        db.session.commit()
        login_user(user)
        flash(f'Admin account created successfully. Welcome, {full_name}!', 'success')
        return redirect(url_for('admin_routes.dashboard'))
    return render_template('auth/register.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main_routes.index'))
