"""Encryption, OTP, and cloud storage utilities."""
import os
import random
import string
from datetime import datetime
from cryptography.fernet import Fernet
from flask import current_app

def _get_cipher():
    key = current_app.config.get('SECRET_KEY', 'default-key').encode()
    from base64 import urlsafe_b64encode
    from hashlib import sha256
    k = urlsafe_b64encode(sha256(key).digest())
    return Fernet(k)

def encrypt_value(plain_text):
    if not plain_text:
        return None
    try:
        c = _get_cipher()
        return c.encrypt(plain_text.encode('utf-8'))
    except Exception:
        return None

def decrypt_value(cipher_text):
    if not cipher_text:
        return None
    try:
        c = _get_cipher()
        return c.decrypt(cipher_text).decode('utf-8')
    except Exception:
        return None

def hash_password(plain):
    import bcrypt
    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt())

def check_password(plain, hashed):
    import bcrypt
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed)
    except Exception:
        return False

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def otp_expiry_minutes():
    return 10

def send_otp_email(email, otp):
    try:
        if current_app.config.get('MAIL_USERNAME'):
            from flask_mail import Message
            from extensions import mail
            msg = Message(
                'Your Hospital Login OTP',
                sender=current_app.config.get('MAIL_USERNAME'),
                recipients=[email]
            )
            msg.body = f'Your one-time password is: {otp}\n\nIt is valid for {otp_expiry_minutes()} minutes.\n\nDo not share this with anyone.'
            mail.send(msg)
        else:
            print(f'[DEV] OTP for {email}: {otp}')
        return True
    except Exception as e:
        current_app.logger.warning(f'Email OTP send failed: {e}')
        print(f'[DEV] OTP for {email}: {otp}')
        return True

def upload_to_storage(file, folder='reports'):
    """Upload file to S3, Firebase, or local static/uploads. Returns (url, original_filename)."""
    from werkzeug.utils import secure_filename
    fname = secure_filename(file.filename) or 'report'
    if current_app.config.get('AWS_ACCESS_KEY_ID') and current_app.config.get('AWS_S3_BUCKET'):
        try:
            import boto3
            key = f"{folder}/{datetime.utcnow().strftime('%Y%m%d')}_{os.urandom(4).hex()}_{fname}"
            s3 = boto3.client(
                's3',
                aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
                aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY']
            )
            file.seek(0)
            s3.upload_fileobj(file, current_app.config['AWS_S3_BUCKET'], key)
            return f"https://{current_app.config['AWS_S3_BUCKET']}.s3.amazonaws.com/{key}", fname
        except Exception as e:
            current_app.logger.warning(f'S3 upload failed: {e}')
    firebase_creds = current_app.config.get('FIREBASE_CREDENTIALS_PATH')
    if firebase_creds and os.path.isfile(firebase_creds):
        try:
            import firebase_admin
            from firebase_admin import storage
            if not firebase_admin._apps:
                firebase_admin.initialize_app(options={'storageBucket': current_app.config.get('FIREBASE_STORAGE_BUCKET', '')})
            bucket = storage.bucket()
            ext = os.path.splitext(fname)[1] or '.pdf'
            blob = bucket.blob(f"{folder}/{datetime.utcnow().strftime('%Y%m%d')}_{os.urandom(4).hex()}{ext}")
            file.seek(0)
            blob.upload_from_file(file, content_type=file.content_type or 'application/octet-stream')
            blob.make_public()
            return blob.public_url, fname
        except Exception as e:
            current_app.logger.warning(f'Firebase upload failed: {e}')
    import uuid
    ext = os.path.splitext(fname)[1] or '.pdf'
    safe = f"{folder}/{uuid.uuid4().hex}{ext}"
    base = os.path.join(current_app.static_folder, 'uploads')
    os.makedirs(base, exist_ok=True)
    path = os.path.join(base, safe)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    file.save(path)
    return f'/static/uploads/{safe}', fname

def create_record_hash(record_type, record_id, data_str):
    """Simple blockchain-like record linking."""
    try:
        from extensions import db
        from models import RecordHash
        import hashlib
        
        # Get the previous hash for this type
        prev = RecordHash.query.filter_by(record_type=record_type).order_by(RecordHash.id.desc()).first()
        prev_hash = prev.current_hash if prev else "0" * 64
        
        # Create current hash
        raw = f"{record_type}:{record_id}:{data_str}:{prev_hash}"
        curr_hash = hashlib.sha256(raw.encode()).hexdigest()
        
        new_hash = RecordHash(
            record_type=record_type,
            record_id=record_id,
            current_hash=curr_hash,
            previous_hash=prev_hash
        )
        db.session.add(new_hash)
        db.session.commit()
    except Exception as e:
        print(f"Blockchain error: {e}")
