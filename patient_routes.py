"""Patient portal: appointments, prescriptions, reports, and accessibility helpers."""
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import (
    User, PatientProfile, DoctorProfile, Appointment, Prescription, MedicalReport, CallbackRequest
)
import os

import os
from gemini_service import predict_waiting_time, suggest_appointment

bp = Blueprint('patient_routes', __name__)

def patient_required(f):
    from functools import wraps
    @wraps(f)
    def inner(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'patient':
            flash('Access denied. Patient login required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return inner

@bp.route('/dashboard')
@login_required
@patient_required
def dashboard():
    appointments = Appointment.query.filter_by(patient_id=current_user.id).order_by(
        Appointment.appointment_date.desc(), Appointment.appointment_time.desc()
    ).limit(10).all()
    return render_template('patient/dashboard.html', appointments=appointments)

@bp.route('/doctors')
@login_required
@patient_required
def doctors():
    doctors = DoctorProfile.query.join(User).filter(User.id == DoctorProfile.user_id).all()
    return render_template('patient/doctors.html', doctors=doctors)

@bp.route('/book-appointment', methods=['GET', 'POST'])
@login_required
@patient_required
def book_appointment():
    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id', type=int)
        appt_date = request.form.get('appointment_date')
        appt_time = request.form.get('appointment_time')
        notes = request.form.get('notes', '').strip()
        if not doctor_id or not appt_date or not appt_time:
            flash('Please select doctor, date and time.', 'danger')
            return redirect(url_for('patient_routes.book_appointment'))
        try:
            d = datetime.strptime(appt_date, '%Y-%m-%d').date()
            t = datetime.strptime(appt_time, '%H:%M').time()
        except ValueError:
            flash('Invalid date or time.', 'danger')
            return redirect(url_for('patient_routes.book_appointment'))
        if d < date.today():
            flash('Cannot book in the past.', 'danger')
            return redirect(url_for('patient_routes.book_appointment'))
        doctor = User.query.get(doctor_id)
        if not doctor or doctor.role != 'doctor':
            flash('Invalid doctor.', 'danger')
            return redirect(url_for('patient_routes.book_appointment'))
        apt = Appointment(patient_id=current_user.id, doctor_id=doctor_id, appointment_date=d, appointment_time=t, notes=notes)
        db.session.add(apt)
        db.session.commit()
        flash('Appointment booked successfully.', 'success')
        return redirect(url_for('patient_routes.appointments'))
    doctors = DoctorProfile.query.join(User).filter(User.id == DoctorProfile.user_id).all()
    return render_template('patient/book_appointment.html', doctors=doctors, today=date.today().isoformat())

@bp.route('/request-callback', methods=['GET', 'POST'])
@login_required
@patient_required
def request_callback():
    """Illiterate-friendly: patient requests a phone call to complete booking."""
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        phone = (request.form.get('phone') or '').strip()
        preferred_language = (request.form.get('preferred_language') or '').strip() or None
        preferred_time = (request.form.get('preferred_time') or '').strip() or None
        reason = (request.form.get('reason') or '').strip() or None
        if not phone:
            flash('Please enter your phone number.', 'danger')
            return render_template('patient/request_callback.html')
        req = CallbackRequest(patient_id=current_user.id, preferred_language=preferred_language, preferred_time=preferred_time, reason=reason)
        req.name = name or (current_user.patient_profile.full_name if current_user.patient_profile else None)
        req.phone = phone
        db.session.add(req)
        db.session.commit()
        flash('Request submitted. Hospital will call you soon.', 'success')
        return redirect(url_for('patient_routes.dashboard'))
    return render_template('patient/request_callback.html')

def _estimate_wait_minutes(doctor_id: int, appt_date: date, appt_time_str: str | None = None) -> int:
    """
    Very simple waiting time predictor (MVP):
    waiting_minutes ~= (queue_before_you) * avg_minutes_per_patient + buffer
    """
    avg_minutes = 12  # tweak as needed
    buffer = 5
    q = Appointment.query.filter_by(doctor_id=doctor_id, appointment_date=appt_date).filter(
        Appointment.status.in_(['scheduled'])
    )
    if appt_time_str:
        try:
            t = datetime.strptime(appt_time_str, '%H:%M').time()
            q = q.filter(Appointment.appointment_time <= t)
        except ValueError:
            pass
    queue_count = q.count()
    return int(queue_count * avg_minutes + buffer)

@bp.route('/ai/wait-time')
@login_required
@patient_required
def ai_wait_time():
    doctor_id = request.args.get('doctor_id', type=int)
    appt_date = request.args.get('date') or date.today().isoformat()
    appt_time = request.args.get('time')
    if not doctor_id:
        return jsonify({'ok': False, 'error': 'doctor_id is required'}), 400
    try:
        d = datetime.strptime(appt_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'ok': False, 'error': 'invalid date'}), 400
        
    doctor = User.query.get(doctor_id)
    if not doctor or doctor.role != 'doctor':
         return jsonify({'ok': False, 'error': 'invalid doctor'}), 404
         
    # Fetch real queue data
    queue_count = Appointment.query.filter_by(doctor_id=doctor_id, appointment_date=d, status='scheduled').count()
    queue_info = f"Doctor: {doctor.doctor_profile.full_name}, Specialty: {doctor.doctor_profile.specialization}. Queue: {queue_count} scheduled patients for {appt_date}."
    
    # AI Prediction
    ai_msg = predict_waiting_time(queue_info)
    # Heuristic Fallback/Comparison
    heuristic_minutes = _estimate_wait_minutes(doctor_id, d, appt_time)
    
    return jsonify({
        'ok': True, 
        'estimated_wait_minutes': heuristic_minutes,
        'ai_prediction': ai_msg
    })

@bp.route('/ai/suggest-slot')
@login_required
@patient_required
def ai_suggest_slot():
    """Smart appointment optimization (MVP heuristics): pick available doctor with shortest queue."""
    specialization = (request.args.get('specialization') or '').strip()
    appt_date_str = request.args.get('date') or date.today().isoformat()
    try:
        d = datetime.strptime(appt_date_str, '%Y-%m-%d').date()
    except ValueError:
        d = date.today()

    dq = DoctorProfile.query.join(User).filter(User.role == 'doctor')
    if specialization:
        dq = dq.filter(DoctorProfile.specialization.ilike(f'%{specialization}%'))
    doctors = dq.all()
    if not doctors:
        return jsonify({'ok': False, 'error': 'no doctors found'}), 404

    best = None
    for doc in doctors:
        if not doc.is_available:
            continue
        wait = _estimate_wait_minutes(doc.user_id, d)
        if best is None or wait < best['estimated_wait_minutes']:
            # suggest a time: next available block from now-ish within timings if set
            suggested_time = '10:00'
            if doc.available_from:
                suggested_time = doc.available_from.strftime('%H:%M')
            best = {
                'doctor_id': doc.user_id,
                'doctor_name': doc.full_name,
                'specialization': doc.specialization,
                'date': d.isoformat(),
                'suggested_time': suggested_time,
                'estimated_wait_minutes': wait,
            }
    if not best:
        return jsonify({'ok': False, 'error': 'no available doctors'}), 404
    return jsonify({'ok': True, 'suggestion': best})

@bp.route('/appointments')
@login_required
@patient_required
def appointments():
    appointments = Appointment.query.filter_by(patient_id=current_user.id).order_by(
        Appointment.appointment_date.desc(), Appointment.appointment_time.desc()
    ).all()
    return render_template('patient/appointments.html', appointments=appointments)

@bp.route('/prescriptions')
@login_required
@patient_required
def prescriptions():
    presc = Prescription.query.filter_by(patient_id=current_user.id).order_by(Prescription.created_at.desc()).all()
    return render_template('patient/prescriptions.html', prescriptions=presc)

@bp.route('/reports')
@login_required
@patient_required
def reports():
    reports = MedicalReport.query.filter_by(patient_id=current_user.id).order_by(MedicalReport.created_at.desc()).all()
    return render_template('patient/reports.html', reports=reports)

@bp.route('/report/<int:report_id>/download')
@login_required
@patient_required
def download_report(report_id):
    r = MedicalReport.query.filter_by(id=report_id, patient_id=current_user.id).first()
    if not r:
        flash('Report not found.', 'danger')
        return redirect(url_for('patient_routes.reports'))
    if r.file_url.startswith('/'):
        from flask import current_app
        path = os.path.join(current_app.static_folder, r.file_url.replace('/static/', ''))
        if os.path.isfile(path):
            return send_file(path, as_attachment=True, download_name=r.file_name or 'report')
    return redirect(r.file_url)
