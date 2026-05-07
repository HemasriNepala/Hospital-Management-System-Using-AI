"""Doctor portal: schedule, prescriptions, upload reports, and AI helpers."""
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import User, DoctorProfile, Appointment, Prescription, MedicalReport, PatientProfile
from utils import upload_to_storage, create_record_hash
from gemini_service import generate_health_summary

bp = Blueprint('doctor_routes', __name__)

def doctor_required(f):
    from functools import wraps
    @wraps(f)
    def inner(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'doctor':
            flash('Access denied. Doctor login required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return inner

@bp.route('/dashboard')
@login_required
@doctor_required
def dashboard():
    today = date.today()
    appointments = Appointment.query.filter_by(doctor_id=current_user.id).filter(
        Appointment.appointment_date >= today
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).limit(15).all()
    return render_template('doctor/dashboard.html', appointments=appointments)

@bp.route('/schedule')
@login_required
@doctor_required
def schedule():
    appointments = Appointment.query.filter_by(doctor_id=current_user.id).order_by(
        Appointment.appointment_date.desc(), Appointment.appointment_time.desc()
    ).all()
    return render_template('doctor/schedule.html', appointments=appointments)

@bp.route('/availability', methods=['GET', 'POST'])
@login_required
@doctor_required
def availability():
    profile = DoctorProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        flash('Profile not found.', 'danger')
        return redirect(url_for('doctor_routes.dashboard'))
    if request.method == 'POST':
        profile.available_from = datetime.strptime(request.form.get('available_from') or '09:00', '%H:%M').time()
        profile.available_to = datetime.strptime(request.form.get('available_to') or '17:00', '%H:%M').time()
        profile.is_available = request.form.get('is_available') == 'yes'
        db.session.commit()
        flash('Availability updated.', 'success')
        return redirect(url_for('doctor_routes.availability'))
    return render_template('doctor/availability.html', profile=profile)

@bp.route('/appointment/<int:apt_id>/prescription', methods=['GET', 'POST'])
@login_required
@doctor_required
def add_prescription(apt_id):
    apt = Appointment.query.filter_by(id=apt_id, doctor_id=current_user.id).first()
    if not apt:
        flash('Appointment not found.', 'danger')
        return redirect(url_for('doctor_routes.schedule'))
    if request.method == 'POST':
        medicines = request.form.get('medicines', '').strip()
        instructions = request.form.get('instructions', '').strip()
        diagnosis = request.form.get('diagnosis', '').strip()
        presc = Prescription(
            appointment_id=apt.id, patient_id=apt.patient_id, doctor_id=current_user.id,
            medicines=medicines, instructions=instructions, diagnosis=diagnosis
        )
        db.session.add(presc)
        apt.status = 'completed'
        db.session.commit()
        
        # Add to Blockchain-style ledger
        create_record_hash('prescription', presc.id, f"{medicines}_{diagnosis}")
        
        flash('Prescription added. (Blockchain Verified)', 'success')
        return redirect(url_for('doctor_routes.schedule'))
    return render_template('doctor/add_prescription.html', appointment=apt)

@bp.route('/appointment/<int:apt_id>/upload-report', methods=['GET', 'POST'])
@login_required
@doctor_required
def upload_report(apt_id):
    apt = Appointment.query.filter_by(id=apt_id, doctor_id=current_user.id).first()
    if not apt:
        flash('Appointment not found.', 'danger')
        return redirect(url_for('doctor_routes.schedule'))
    if request.method == 'POST':
        file = request.files.get('report_file')
        report_type = request.form.get('report_type') or 'General'
        notes = request.form.get('notes', '').strip()
        if not file or not file.filename:
            flash('Please select a file.', 'danger')
            return render_template('doctor/upload_report.html', appointment=apt)
        url, fname = upload_to_storage(file, folder='reports')
        if url:
            r = MedicalReport(patient_id=apt.patient_id, doctor_id=current_user.id, report_type=report_type, file_url=url, file_name=fname, notes=notes)
            db.session.add(r)
            db.session.commit()
            flash('Report uploaded.', 'success')
            return redirect(url_for('doctor_routes.schedule'))
        flash('Upload failed. Try again.', 'danger')
    return render_template('doctor/upload_report.html', appointment=apt)


def _simple_health_summary(patient_user_id: int) -> dict:
    """MVP 'AI' summary generator: rule-based, short, doctor-friendly."""
    patient = User.query.get(patient_user_id)
    prof = PatientProfile.query.filter_by(user_id=patient_user_id).first()
    last_appts = Appointment.query.filter_by(patient_id=patient_user_id).order_by(
        Appointment.appointment_date.desc(), Appointment.appointment_time.desc()
    ).limit(5).all()
    last_presc = Prescription.query.filter_by(patient_id=patient_user_id).order_by(
        Prescription.created_at.desc()
    ).limit(5).all()
    reports_count = MedicalReport.query.filter_by(patient_id=patient_user_id).count()

    summary_lines = []
    if prof:
        summary_lines.append(f"Name: {prof.full_name}")
        if prof.gender:
            summary_lines.append(f"Gender: {prof.gender}")
        if prof.blood_group:
            summary_lines.append(f"Blood Group: {prof.blood_group}")
        if prof.date_of_birth:
            summary_lines.append(f"DOB: {prof.date_of_birth}")
    summary_lines.append(f"Reports uploaded: {reports_count}")
    if last_presc:
        dx = [p.diagnosis for p in last_presc if p.diagnosis]
        if dx:
            summary_lines.append("Recent diagnosis: " + "; ".join(dx[:3]))
    if last_appts:
        summary_lines.append(f"Recent visits: {len(last_appts)} (latest on {last_appts[0].appointment_date.strftime('%d-%b-%Y')})")

    return {
        'patient_id': patient_user_id,
        'patient_email': patient.email if patient else None,
        'summary_text': "\n".join(summary_lines).strip()
    }

@bp.route('/ai/patient-summary/<int:patient_id>')
@login_required
@doctor_required
def ai_patient_summary(patient_id):
    # Gather patient health history
    prescs = Prescription.query.filter_by(patient_id=patient_id).order_by(Prescription.created_at.desc()).all()
    reports = MedicalReport.query.filter_by(patient_id=patient_id).order_by(MedicalReport.created_at.desc()).all()
    
    history_data = "Recent Diagnoses and Medicines:\n"
    for p in prescs[:5]:
        history_data += f"- {p.diagnosis}: {p.medicines} ({p.instructions})\n"
    history_data += "\nMedical Reports:\n"
    for r in reports[:3]:
        history_data += f"- {r.report_type}: {r.notes}\n"
    
    summary = generate_health_summary(history_data or "No prior record found for this patient.")
    return jsonify({'ok': True, 'summary': summary})
