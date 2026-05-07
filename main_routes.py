"""Main landing and home routes."""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

bp = Blueprint('main_routes', __name__)

@bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_routes.dashboard'))
        if current_user.role == 'doctor':
            return redirect(url_for('doctor_routes.dashboard'))
        return redirect(url_for('patient_routes.dashboard'))
    return render_template('index.html')

@bp.route('/set-language/<lang>')
def set_language(lang):
    from flask import session, request
    if lang in ['en', 'te', 'hi']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('main_routes.index'))
