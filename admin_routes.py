"""Admin portal: manage doctors, patients, appointments, reports, and smart operations."""
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import User, PatientProfile, DoctorProfile, Appointment, MedicalReport, CallbackRequest, Bed

bp = Blueprint('admin_routes', __name__)

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def inner(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin login required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return inner

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    doctors_count = User.query.filter_by(role='doctor').count()
    patients_count = User.query.filter_by(role='patient').count()
    today = date.today()
    appointments_today = Appointment.query.filter(Appointment.appointment_date == today).count()
    beds_total = Bed.query.count()
    beds_available = Bed.query.filter_by(status='available').count()
    callback_new = CallbackRequest.query.filter_by(status='new').count()
    return render_template('admin/dashboard.html',
        doctors_count=doctors_count,
        patients_count=patients_count,
        appointments_today=appointments_today,
        beds_total=beds_total,
        beds_available=beds_available,
        callback_new=callback_new
    )

@bp.route('/doctors')
@login_required
@admin_required
def doctors():
    doctors = DoctorProfile.query.join(User).filter(User.id == DoctorProfile.user_id).all()
    return render_template('admin/doctors.html', doctors=doctors)

@bp.route('/doctors/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_doctor():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        full_name = (request.form.get('full_name') or '').strip()
        phone = (request.form.get('phone') or '').strip()
        specialization = (request.form.get('specialization') or 'General').strip()
        qualification = (request.form.get('qualification') or '').strip()
        if not email or not password or not full_name:
            flash('Email, password and full name are required.', 'danger')
            return render_template('admin/add_doctor.html')
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return render_template('admin/add_doctor.html')
        user = User(email=email, role='doctor')
        user.password = password
        user.is_verified = True
        db.session.add(user)
        db.session.flush()
        profile = DoctorProfile(user_id=user.id, full_name=full_name, phone=phone, specialization=specialization, qualification=qualification)
        db.session.add(profile)
        db.session.commit()
        flash('Doctor added.', 'success')
        return redirect(url_for('admin_routes.doctors'))
    return render_template('admin/add_doctor.html')

@bp.route('/patients')
@login_required
@admin_required
def patients():
    patients = PatientProfile.query.join(User).filter(User.id == PatientProfile.user_id).all()
    return render_template('admin/patients.html', patients=patients)

@bp.route('/appointments')
@login_required
@admin_required
def appointments():
    appointments = Appointment.query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
    return render_template('admin/appointments.html', appointments=appointments)

@bp.route('/reports')
@login_required
@admin_required
def reports():
    doctors_count = User.query.filter_by(role='doctor').count()
    patients_count = User.query.filter_by(role='patient').count()
    appointments_count = Appointment.query.count()
    return render_template('admin/reports.html', doctors_count=doctors_count, patients_count=patients_count, appointments_count=appointments_count)


@bp.route('/callbacks', methods=['GET', 'POST'])
@login_required
@admin_required
def callbacks():
    """View and update callback requests (help illiterate users)."""
    if request.method == 'POST':
        req_id = request.form.get('request_id', type=int)
        status = (request.form.get('status') or '').strip()
        r = CallbackRequest.query.get(req_id) if req_id else None
        if r and status in ('new', 'called', 'closed'):
            r.status = status
            db.session.commit()
            flash('Callback request updated.', 'success')
        return redirect(url_for('admin_routes.callbacks'))
    items = CallbackRequest.query.order_by(CallbackRequest.created_at.desc()).limit(200).all()
    return render_template('admin/callbacks.html', items=items)


@bp.route('/beds', methods=['GET', 'POST'])
@login_required
@admin_required
def beds():
    """Emergency bed availability system (real-time via admin updates)."""
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            ward = (request.form.get('ward') or '').strip()
            bed_number = (request.form.get('bed_number') or '').strip()
            status = (request.form.get('status') or 'available').strip()
            if not ward or not bed_number:
                flash('Ward and bed number are required.', 'danger')
                return redirect(url_for('admin_routes.beds'))
            b = Bed(ward=ward, bed_number=bed_number, status=status)
            b.notes = (request.form.get('notes') or '').strip() or None
            db.session.add(b)
            try:
                db.session.commit()
                flash('Bed added.', 'success')
            except Exception:
                db.session.rollback()
                flash('Bed already exists for this ward/number.', 'danger')
            return redirect(url_for('admin_routes.beds'))
        if action == 'update':
            bed_id = request.form.get('bed_id', type=int)
            status = (request.form.get('status') or '').strip()
            notes = (request.form.get('notes') or '').strip() or None
            b = Bed.query.get(bed_id) if bed_id else None
            if b and status in ('available', 'occupied', 'cleaning', 'maintenance'):
                b.status = status
                b.notes = notes
                db.session.commit()
                flash('Bed updated.', 'success')
            return redirect(url_for('admin_routes.beds'))

    beds = Bed.query.order_by(Bed.ward.asc(), Bed.bed_number.asc()).all()
    return render_template('admin/beds.html', beds=beds)

@bp.route('/doctors/delete/<int:doc_id>')
@login_required
@admin_required
def delete_doctor(doc_id):
    doc = DoctorProfile.query.get(doc_id)
    if not doc:
        flash('Doctor not found.', 'danger')
    else:
        user = User.query.get(doc.user_id)
        db.session.delete(doc)
        if user:
            db.session.delete(user)
        db.session.commit()
        flash('Doctor and associated user removed.', 'success')
    return redirect(url_for('admin_routes.doctors'))

@bp.route('/patients/delete/<int:pat_id>')
@login_required
@admin_required
def delete_patient(pat_id):
    profile = PatientProfile.query.get(pat_id)
    if not profile:
        flash('Patient not found.', 'danger')
    else:
        user = User.query.get(profile.user_id)
        db.session.delete(profile)
        if user:
            db.session.delete(user)
        db.session.commit()
        flash('Patient and associated user removed.', 'success')
    return redirect(url_for('admin_routes.patients'))

@bp.route('/appointments/delete/<int:apt_id>')
@login_required
@admin_required
def delete_appointment(apt_id):
    apt = Appointment.query.get(apt_id)
    if apt:
        db.session.delete(apt)
        db.session.commit()
        flash('Appointment removed.', 'success')
    return redirect(url_for('admin_routes.appointments'))

@bp.route('/beds/delete/<int:bed_id>')
@login_required
@admin_required
def delete_bed(bed_id):
    bed = Bed.query.get(bed_id)
    if bed:
        db.session.delete(bed)
        db.session.commit()
        flash('Bed removed.', 'success')
    return redirect(url_for('admin_routes.beds'))

@bp.route('/callbacks/delete/<int:call_id>')
@login_required
@admin_required
def delete_callback(call_id):
    req = CallbackRequest.query.get(call_id)
    if req:
        db.session.delete(req)
        db.session.commit()
        flash('Callback request removed.', 'success')
    return redirect(url_for('admin_routes.callbacks'))
