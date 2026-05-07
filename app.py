"""Flask application factory - all in project folder."""
from flask import Flask, session
from config import Config
from extensions import db, login_manager, mail, csrf

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(config_class)
    app.config.setdefault('WTF_CSRF_ENABLED', True)
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to continue.'

    from translations import translate
    app.jinja_env.globals.update(t=translate)

    from models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from main_routes import bp as main_bp
    from auth import bp as auth_bp
    from patient_routes import bp as patient_bp
    from doctor_routes import bp as doctor_bp
    from admin_routes import bp as admin_bp
    from ai_routes import bp as ai_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(patient_bp, url_prefix='/patient')
    app.register_blueprint(doctor_bp, url_prefix='/doctor')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(ai_bp, url_prefix='/ai')

    # Language Middleware (Simple)
    @app.before_request
    def set_language():
        if 'lang' not in session:
            session['lang'] = 'en'

    with app.app_context():
        db.create_all()

    return app
