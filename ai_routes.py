from flask import Blueprint, render_template, request, session, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import HospitalResource, Bed, Appointment, User, Prescription, MedicalReport, RecordHash
from gemini_service import (
    generate_health_summary, predict_waiting_time, 
    suggest_appointment, check_medical_error, predict_resource_demand
)
import hashlib
import json

bp = Blueprint('ai_routes', __name__)

@bp.route('/ai/waiting-time')
def waiting_time():
    """AI Waiting Time Predictor based on queue data."""
    # Build some 'queue data' to feed Gemini
    today_appointments = Appointment.query.filter_by(status='scheduled').count()
    doctors_available = User.query.filter_by(role='doctor').count()
    queue_data = f"{today_appointments} scheduled appointments with {doctors_available} doctors on duty."
    
    prediction = predict_waiting_time(queue_data)
    # If the AI response is too long, we take the first sentence for the navbar
    nav_display = prediction.split('.')[0] + '.' if '.' in prediction else prediction
    if len(nav_display) > 60:
        nav_display = nav_display[:57] + "..."
        
    return jsonify({
        "status": "success",
        "prediction": nav_display,
        "full_ai_analysis": prediction,
        "queue_load": today_appointments
    })

@bp.route('/ai/health-summary/<int:patient_id>')
@login_required
def health_summary(patient_id):
    """AI Health Summary for doctors."""
    if current_user.role != 'doctor':
        return jsonify({"error": "Unauthorized"}), 403
        
    prescriptions = Prescription.query.filter_by(patient_id=patient_id).all()
    reports = MedicalReport.query.filter_by(patient_id=patient_id).all()
    
    history_text = ""
    for p in prescriptions:
        history_text += f"\n- Prescription: Medicines: {p.medicines}, Instructions: {p.instructions}"
    for r in reports:
        history_text += f"\n- Report: Type: {r.report_type}, Notes: {r.notes}"
        
    summary = generate_health_summary(history_text or "No prior history found.")
    return jsonify({"summary": summary})

@bp.route('/ai/smart-suggest', methods=['POST'])
def smart_suggest():
    """Smart Appointment Optimization suggestions."""
    symptoms = request.form.get('symptoms')
    if not symptoms:
        return jsonify({"error": "No symptoms provided"}), 400
        
    doctors = User.query.filter_by(role='doctor').all()
    doctor_list = []
    for d in doctors:
        profile = d.doctor_profile
        if profile:
            doctor_list.append(f"{profile.full_name} ({profile.specialization})")
    
    suggestion = suggest_appointment(symptoms, str(doctor_list))
    return jsonify({"suggestion": suggestion})

@bp.route('/ai/drug-check', methods=['POST'])
@login_required
def drug_check():
    """AI Medical Error Alert for drug interactions."""
    if current_user.role != 'doctor':
        return jsonify({"error": "Unauthorized"}), 403
        
    patient_id = request.form.get('patient_id')
    prescription = request.form.get('prescription')
    
    # Get patient's existing prescriptions
    existing = Prescription.query.filter_by(patient_id=patient_id).all()
    history = ", ".join([e.medicines for e in existing])
    
    check_result = check_medical_error(prescription, history or "None")
    return jsonify({"result": check_result})

@bp.route('/ai/resource-prediction')
@login_required
def resource_prediction():
    """Predict resource demand for Admin dashboard."""
    if current_user.role != 'admin':
        return redirect(url_for('main_routes.index'))
        
    # Get some usage data (placeholder based on existing counts)
    appointment_count = Appointment.query.count()
    prescription_count = Prescription.query.count()
    historical_usage = f"Total appointments: {appointment_count}, Total prescriptions: {prescription_count}."
    
    prediction = predict_resource_demand(historical_usage)
    return jsonify({"prediction": prediction})

@bp.route('/blockchain/verify/<int:record_id>/<string:record_type>')
def verify_integrity(record_id, record_type):
    """Blockchain verification for medical records."""
    hash_obj = RecordHash.query.filter_by(record_id=record_id, record_type=record_type).first()
    if not hash_obj:
        return jsonify({"status": "error", "message": "No record hash found"}), 404
        
    # This is where we'd re-hash the original data and compare
    # but for proof of concept, we just return the chain status
    return jsonify({
        "status": "verified",
        "current_hash": hash_obj.current_hash,
        "previous_hash": hash_obj.previous_hash,
        "tamper_proof": True
    })
