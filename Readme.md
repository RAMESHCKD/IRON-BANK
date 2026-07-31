# IronBank Banking Application

IronBank is a Flask-based banking administration application. It provides an administrator with tools to manage customer records, balances, transactions, KYC information, cheque books, and cheque status. Customer-facing login and dashboard routes are disabled in the current version.

## Current Features

### Administrator access

- Login with password and email OTP verification.
- Dashboard with account statistics and recent transactions.
- Add customer records with PAN validation.
- Customer lookup by account number or user ID.
- Customer summary with balance, contact information, and KYC status.
- Deposit and withdrawal processing.
- Transaction audit logs.
- KYC and C-KYC management.
- AKYC number generation after valid PAN submission.
- PAN values are uppercase and validated as `ABCDE1234F`.
- PAN editing is allowed only when KYC is rejected.
- Cheque-book request and cancellation management.
- Cheque lookup by cheque number.
- Cheque statuses: `Unused`, `Used`, `Passed`, and `Blocked`.
- PDF download for filtered customer transactions, statements, and passbook views.

Customer records remain in the database for administrator management, but customer-side login and dashboard access are not enabled.

## Technology

- Python 3
- Flask 3
- Flask-SQLAlchemy
- SQLite
- Jinja templates
- HTML, CSS, and JavaScript
- `python-dotenv`
- Werkzeug password hashing
- SMTP for OTP delivery

## Project Structure

```text
Banking Application/
|-- app.py                         Application factory and database setup
|-- config.py                      Environment and SQLite configuration
|-- requirements.txt               Python dependencies
|-- .env.example                   SMTP configuration template
|-- models/
|   `-- db_models.py                User, Transaction, Cheque, and OTP models
|-- routes/
|   |-- auth.py                     Login, OTP, and logout routes
|   |-- admin.py                    Administrator routes
|   `-- customer.py                 Retained legacy customer routes, not registered
|-- templates/
|   |-- base.html                   Shared authenticated layout and public navbar
|   |-- login.html                  Administrator login
|   |-- otp.html                    OTP verification
|   `-- admin/                      Administrator screens
|-- static/
|   |-- css/style.css               Application styling
|   `-- js/main.js                  Shared browser behavior
`-- database/banking.db             SQLite database created by the application
```

## Installation

Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start the application:

```powershell
python app.py
```

Open `http://127.0.0.1:5000` in a browser.

The application creates `database/banking.db` automatically and creates or updates the required tables and profile columns on startup.

## SMTP OTP Configuration

Copy `.env.example` to `.env` and replace the placeholders:

```powershell
Copy-Item .env.example .env
```

Example Gmail configuration:

```env
SECRET_KEY=replace-with-a-long-random-secret
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-gmail-address@gmail.com
MAIL_PASSWORD=your-16-character-google-app-password
```

Use a Google App Password, not the normal Gmail password. The Gmail account must have two-step verification enabled before an App Password can be created.

The OTP is stored temporarily in the `otps` table and is sent to the administrator email address. The OTP is not displayed in the browser or in application flash messages.

Never commit `.env` or expose `MAIL_PASSWORD` in source control. The repository `.gitignore` excludes `.env`.

## Authentication Flow

```text
Administrator enters user ID and password
      |
Password is verified
      |
OTP is generated and emailed
      |
Administrator enters the OTP
      |
Administrator dashboard
```

The login page uses a public top navbar. Authenticated administrator pages use the administrator sidebar and highlight the current navigation item.

## Database Tables

### `users`

Stores administrator and customer records, including account number, balance, contact details, password hash, PAN, C-KYC, AKYC, KYC status, and cheque-book request status.

### `transactions`

Stores deposits and withdrawals with account number, transaction type, amount, resulting balance, and timestamp.

### `cheques`

Stores cheque number, account number, customer name, amount, issue date, status, and remarks.

### `otps`

Stores the temporary OTP email, code, expiration time, and whether the OTP was verified. OTP records should be treated as sensitive data.

## Default Administrator

The application ensures an administrator record exists with user ID `admin`. The current password and email are configured by the startup seed/update logic and should be changed for any real deployment.

This project is intended for educational and local development use. It is not production banking software.

## 📖 Future Enhancements

- Money Transfer
- Fund Transfer Between Accounts
- Beneficiary Management
- Debit Card Management
- Account Statements (PDF)
- Profile Picture Upload
- Dark Mode
- SMS OTP
- Two-Factor Authentication
- Admin Analytics Dashboard
- MySQL Support
- Docker Deployment

---

## 🎯 Learning Outcomes

This project demonstrates:

- Object-Oriented Programming (OOP)
- Flask Web Development
- RESTful Routing
- Database Design
- Authentication & Authorization
- Email OTP Verification
- Session Management
- Password Hashing
- Frontend Development
- CRUD Operations
- MVC Project Structure
- Full-Stack Development

---

## 👨‍💻 Developed By

**Ramesh Choudhary**

**Project:** Banking Application (IronBank)

Developed as a college project to demonstrate full-stack web development using Python Flask and modern web technologies.

---

## 📄 License

This project is developed for educational purposes only.

It is not intended for production or real-world banking use.