# Hospital Management System (MVP)

A simple Hospital Management website with **Patient**, **Doctor**, and **Admin** portals. Built with HTML, CSS, JavaScript, Bootstrap, and Flask (Python). Uses MySQL and optional cloud storage (AWS S3 / Firebase) for reports.

## Features

- **Patient:** Register, book appointments, view doctors, prescriptions, and download reports.
- **Accessibility:** Patient can request a **phone call** for booking help (for illiterate/elderly users).
- **Doctor:** View schedule, add prescriptions, upload reports, set availability.
- **AI/Smart helpers (MVP-level):**
  - **Waiting Time Predictor:** shows estimated waiting minutes when booking.
  - **Smart Appointment Suggestion:** suggests best doctor/slot with shortest queue.
  - **Health Summary Generator:** doctor can view a quick summary of patient history.
  - **Voice-to-Prescription:** doctor can speak medicines/instructions (browser speech).
  - **Medical Safety Warning (basic):** warns for a few risky medicine combinations (extendable).
- **Admin:** Manage doctors and patients, view appointments, basic reports.
- **Emergency Bed Availability:** track beds (available/occupied/cleaning/maintenance).
- **Language switcher:** UI supports English + Telugu + Hindi (client-side; extendable).
- **Security:** Role-based login, OTP/Email verification, encrypted storage for sensitive data.

## Tech Stack

- **Frontend:** HTML, CSS, JavaScript, Bootstrap 5
- **Backend:** Python Flask
- **Database:** MySQL
- **Storage:** AWS S3 or local `static/uploads` for medical reports
- **Auth:** Flask-Login, bcrypt, OTP via email

## Setup

### 1. Install Python dependencies

```bash
cd "hospital management"
pip install -r requirements.txt
```

### 2. Database

**Option A – Quick start (SQLite, no MySQL):**  
Create a `.env` file and set:

```
USE_SQLITE=1
SECRET_KEY=any-random-secret-key
```

**Option B – MySQL:**  
Create a database:

```sql
CREATE DATABASE hospital_management;
```

Copy `.env.example` to `.env` and set:

- `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`
- `SECRET_KEY` (random string for sessions/encryption)
- Optional: `MAIL_USERNAME`, `MAIL_PASSWORD` for OTP email
- Optional: AWS keys and bucket for report uploads

### 3. Create admin user

```bash
# Windows
set ADMIN_EMAIL=admin@hospital.com
set ADMIN_PASSWORD=your_password
python create_admin.py

# Or leave default: admin@hospital.com / admin123 (change after first login)
python create_admin.py
```

### 4. Run the app

```bash
python run.py
```

Open http://127.0.0.1:5000

## Usage

- **Home:** Choose “I am a Patient”, “I am a Doctor”, or “I am Admin” and Log In or Sign Up.
- **Patients:** Sign Up as Patient → verify OTP → Book Appointment, view Prescriptions and Reports.
- **Patients (illiterate help):** Patient Dashboard → **Request a Phone Call** → Admin sees it in **Call Requests**.
- **Doctors:** Added by Admin (or register as Doctor) → set timings → add prescriptions and upload reports for appointments.
- **Doctors (AI):** Doctor Schedule → click **Health Summary** beside a patient.
- **Doctors (voice):** Add Prescription → use **Speak Medicines / Speak Instructions**.
- **Admin:** Log in as admin → add doctors, view patients and appointments, basic reports.
- **Admin (beds):** Admin Dashboard → **Emergency Beds** to add/update bed status.

## Project structure (all files in project folder)

- `app.py` – Flask app factory
- `config.py` – Configuration from env
- `extensions.py` – db, login_manager, mail, csrf
- `models.py` – Database models
- `utils.py` – Encryption, OTP, file upload (S3/Firebase/local)
- `auth.py`, `main_routes.py`, `patient_routes.py`, `doctor_routes.py`, `admin_routes.py` – Blueprints
- `run.py` – Entry point
- `create_admin.py` – Create first admin user
- `templates/` – HTML (auth, patient, doctor, admin)
- `static/` – CSS, JS, uploads

## Security notes

- Passwords are hashed with bcrypt; sensitive profile fields are encrypted in the database.
- Use HTTPS and strong `SECRET_KEY` in production.
- Set mail credentials for real OTP delivery; otherwise OTP is printed in console for development.
