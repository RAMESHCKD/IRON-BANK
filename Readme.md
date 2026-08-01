# IronBank Banking Application

IronBank is a Flask-based banking admin portal built for managing customer accounts, transactions, KYC validation, and cheque operations. The current version is focused on administrator workflows and includes email-based OTP login for secure access.

## Current Status

- Admin login is enabled and secured with email OTP verification.
- Customer login and customer dashboard routes are intentionally disabled in the current build.
- The application seeds a default admin account automatically on startup.
- SQLite is used for persistence, with automatic table and profile-column updates on app startup.

## Core Features

### Administrator Dashboard

- Secure admin login with user ID + password + OTP verification
- Dashboard summary cards for customer count, account totals, and recent transactions
- Recent transaction activity feed
- Quick access to managing customer records and banking operations

### Customer Management

- Add new customer profiles with validation for name, phone, email, address, and PAN
- Search customers by account number or user ID
- View selected customer profile details and account history
- Update customer records such as name, email, contact, user ID, and PIN
- Track customer balances centrally from the admin panel

### KYC and Profile Controls

- PAN validation in the format ABCDE1234F
- Auto-generation of CKYC and AKYC identifiers
- KYC status tracking with Pending / Approved / Rejected states
- Restricts PAN edits unless KYC was previously rejected
- Customer profile data is stored in the database for admin-side review and updates

### Deposit and Withdrawal

- Cash deposit processing
- Cheque deposit processing with cheque number and date validation
- Withdrawal checks against available balance
- Automatic transaction logging with running balances

### Cheque Management

- Cheque lookup by cheque number
- Cheque statuses: Unused, Used, Passed, Blocked
- Cheque book request and cancel request handling for a customer
- Admin can mark cheques as passed or blocked

### Audit and Reporting

- Transaction audit log page
- Customer transaction history views
- Dashboard totals and recent activity monitoring
- Admin can clear transaction logs from the dashboard panel

## Tech Stack

- Python 3
- Flask 3
- Flask-SQLAlchemy
- SQLite
- Jinja2 templates
- HTML, CSS, and JavaScript
- python-dotenv
- Werkzeug password hashing
- SMTP email delivery for OTP messages

## Project Structure

```text
Banking Application/
├── app.py                    # Flask app setup and DB bootstrapping
├── config.py                 # Environment settings and SQLite configuration
├── Readme.md                 # Project documentation
├── requirements.txt          # Python dependencies
├── .env                      # Local environment config (not committed)
├── database/
│   └── banking.db            # SQLite database file
├── models/
│   └── db_models.py          # SQLAlchemy models for User, Transaction, Cheque, OTP
├── routes/
│   ├── auth.py               # Login, OTP, resend OTP, logout
│   └── admin.py              # Admin dashboard and payment/records management
├── static/
│   ├── css/
│   │   └── style.css         # App styling
│   └── js/
│       └── main.js           # Shared frontend scripting
├── templates/
│   ├── base.html             # Shared layout
│   ├── login.html            # Admin login page
│   ├── otp.html              # OTP verification page
│   └── admin/
│       ├── dashboard.html
│       ├── add_customer.html
│       ├── customers.html
│       ├── deposit.html
│       ├── withdraw.html
│       ├── edit_customer.html
│       ├── transactions.html
│       └── ...
└── .venv/                    # Local virtual environment (optional)
```

## Installation

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create a local environment file named `.env` in the project root:

```env
SECRET_KEY=replace-with-a-long-random-secret
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-gmail-address@gmail.com
MAIL_PASSWORD=your-16-character-google-app-password
```

4. Start the application:

```powershell
python app.py
```

5. Open the app in a browser:

```text
http://127.0.0.1:5000
```

## SMTP and OTP Configuration

- The OTP email is sent using Gmail SMTP settings from the `.env` file.
- Use a Google App Password instead of your normal Gmail password.
- SMTP credentials are required for OTP delivery to work correctly.
- If credentials are missing or invalid, the app will fall back to a warning message and the OTP cannot be delivered.

> Do not commit `.env` or expose your email password in source control.

## Authentication Flow

```text
Admin enters User ID and password
        |
Password validated
        |
OTP is generated and emailed
        |
Admin verifies OTP
        |
Admin dashboard is opened
```

## Default Admin Account

The application seeds a default administrator automatically on first run:

- User ID: admin
- Password: admin@2118
- Email: cbs80200@gmail.com

This default account is intended for local development/testing and should be updated in production deployments.

## Database Design

### `users`

Stores admin and customer data including:

- user ID and account number
- full name and contact info
- password hash
- PIN for customer-level operations
- balance
- role
- PAN, AKYC, CKYC
- KYC status
- cheque book request status

### `transactions`

Stores all transaction events including:

- account number
- transaction type
- amount
- resulting balance
- timestamp

### `cheques`

Stores cheque details such as:

- cheque number
- account number
- customer name
- amount
- issue date
- status
- remarks

### `otps`

Stores short-lived OTP data used during login verification, including:

- email
- generated code
- expiry timestamp
- verified flag

## Notes

- The project is built for educational and local development use.
- It is not a production-grade banking system.
- Customer-side banking flows are intentionally disabled in this version, although the customer model and data remain in the database.

## Future Improvements

Potential enhancements for the project include:

- Fund transfers between accounts
- Beneficiary management
- Debit card management
- PDF account statements
- Profile picture upload
- Dark mode
- SMS OTP support
- Enhanced two-factor authentication
- Better analytics dashboard
- MySQL migration
- Docker deployment

## Learning Outcomes

This project demonstrates:

- Flask web application development
- Database modeling with SQLAlchemy
- Role-based authentication flows
- Password hashing and session management
- Email OTP verification
- Frontend templating with Jinja
- CRUD operations and admin workflows
- Full-stack application structure

## Developer

Developed by Ramesh Choudhary as a banking application project using Python and Flask.

## License

This project is intended for educational use only and is not suitable for real-world banking deployment.