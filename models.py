"""Database models with encrypted sensitive fields."""
from datetime import datetime
from extensions import db
from flask_login import UserMixin
from utils import encrypt_value, decrypt_value

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __table_args__ = (db.UniqueConstraint('email', 'role', name='uix_email_role'),)
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    _password_hash = db.Column('password_hash', db.LargeBinary, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # patient, doctor, admin
    is_verified = db.Column(db.Boolean, default=False)
    otp = db.Column(db.String(6), nullable=True)
    otp_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def password(self):
        raise AttributeError('password is not readable')

    @password.setter
    def password(self, plain):
        from utils import hash_password
        self._password_hash = hash_password(plain)

    def check_password(self, plain):
        from utils import check_password
        return check_password(plain, self._password_hash)

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class PatientProfile(db.Model):
    __tablename__ = 'patient_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    _full_name = db.Column('full_name_enc', db.LargeBinary, nullable=False)
    _phone = db.Column('phone_enc', db.LargeBinary, nullable=True)
    _date_of_birth = db.Column('dob_enc', db.LargeBinary, nullable=True)
    _address = db.Column('address_enc', db.LargeBinary, nullable=True)
    blood_group = db.Column(db.String(10), nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('patient_profile', uselist=False))

    @property
    def full_name(self):
        return decrypt_value(self._full_name) if self._full_name else ''

    @full_name.setter
    def full_name(self, val):
        self._full_name = encrypt_value(str(val)) if val else None

    @property
    def phone(self):
        return decrypt_value(self._phone) if self._phone else None

    @phone.setter
    def phone(self, val):
        self._phone = encrypt_value(str(val)) if val else None

    @property
    def date_of_birth(self):
        return decrypt_value(self._date_of_birth) if self._date_of_birth else None

    @date_of_birth.setter
    def date_of_birth(self, val):
        self._date_of_birth = encrypt_value(str(val)) if val else None

    @property
    def address(self):
        return decrypt_value(self._address) if self._address else None

    @address.setter
    def address(self, val):
        self._address = encrypt_value(str(val)) if val else None


class DoctorProfile(db.Model):
    __tablename__ = 'doctor_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    _full_name = db.Column('full_name_enc', db.LargeBinary, nullable=False)
    _phone = db.Column('phone_enc', db.LargeBinary, nullable=True)
    specialization = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(200), nullable=True)
    is_available = db.Column(db.Boolean, default=True)
    available_from = db.Column(db.Time, nullable=True)
    available_to = db.Column(db.Time, nullable=True)
    consultation_fee = db.Column(db.Numeric(10, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('doctor_profile', uselist=False))

    @property
    def full_name(self):
        return decrypt_value(self._full_name) if self._full_name else ''

    @full_name.setter
    def full_name(self, val):
        self._full_name = encrypt_value(str(val)) if val else None

    @property
    def phone(self):
        return decrypt_value(self._phone) if self._phone else None

    @phone.setter
    def phone(self, val):
        self._phone = encrypt_value(str(val)) if val else None


class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='scheduled')
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    patient = db.relationship('User', foreign_keys=[patient_id])
    doctor = db.relationship('User', foreign_keys=[doctor_id])


class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    _medicines = db.Column('medicines_enc', db.LargeBinary, nullable=True)
    _instructions = db.Column('instructions_enc', db.LargeBinary, nullable=True)
    diagnosis = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    appointment = db.relationship('Appointment', backref='prescription', uselist=False)
    patient = db.relationship('User', foreign_keys=[patient_id])
    doctor = db.relationship('User', foreign_keys=[doctor_id])

    @property
    def medicines(self):
        return decrypt_value(self._medicines) if self._medicines else ''

    @medicines.setter
    def medicines(self, val):
        self._medicines = encrypt_value(str(val)) if val else None

    @property
    def instructions(self):
        return decrypt_value(self._instructions) if self._instructions else ''

    @instructions.setter
    def instructions(self, val):
        self._instructions = encrypt_value(str(val)) if val else None


class MedicalReport(db.Model):
    __tablename__ = 'medical_reports'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    report_type = db.Column(db.String(100), nullable=False)
    file_url = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    patient = db.relationship('User', foreign_keys=[patient_id])
    doctor = db.relationship('User', foreign_keys=[doctor_id])


class CallbackRequest(db.Model):
    """For illiterate/elderly users: request a phone call to help booking."""
    __tablename__ = 'callback_requests'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    _name = db.Column('name_enc', db.LargeBinary, nullable=True)
    _phone = db.Column('phone_enc', db.LargeBinary, nullable=False)
    preferred_language = db.Column(db.String(20), nullable=True)  # e.g., en/te/hi
    preferred_time = db.Column(db.String(50), nullable=True)  # simple human text
    reason = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='new')  # new, called, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    patient = db.relationship('User', foreign_keys=[patient_id])

    @property
    def name(self):
        return decrypt_value(self._name) if self._name else None

    @name.setter
    def name(self, val):
        self._name = encrypt_value(str(val)) if val else None

    @property
    def phone(self):
        return decrypt_value(self._phone) if self._phone else None

    @phone.setter
    def phone(self, val):
        self._phone = encrypt_value(str(val)) if val else None


class Bed(db.Model):
    """Emergency bed availability tracking (simple MVP)."""
    __tablename__ = 'beds'
    id = db.Column(db.Integer, primary_key=True)
    ward = db.Column(db.String(50), nullable=False)  # e.g., ICU, General, Maternity
    bed_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='available')  # available, occupied, cleaning, maintenance
    notes = db.Column(db.String(200), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('ward', 'bed_number', name='uq_bed_ward_number'),
    )

class HospitalResource(db.Model):
    """Resource prediction system (Medicine, staff, equipment)."""
    __tablename__ = 'resources'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # medicine, staff, equipment
    quantity = db.Column(db.Integer, default=0)
    ideal_quantity = db.Column(db.Integer, default=100)
    prediction_next_month = db.Column(db.Integer, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class RecordHash(db.Model):
    """Simple Blockchain-style tamper-proof record link."""
    __tablename__ = 'record_hashes'
    id = db.Column(db.Integer, primary_key=True)
    record_type = db.Column(db.String(50), nullable=False) # prescription, report
    record_id = db.Column(db.Integer, nullable=False)
    current_hash = db.Column(db.String(64), nullable=False)
    previous_hash = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
