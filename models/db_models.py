from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False)
    account_number = db.Column(db.String(20), unique=True, nullable=True) # Null for Admin
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    pin = db.Column(db.Integer, nullable=True) # Transaction PIN for customer
    balance = db.Column(db.Float, default=0.0)
    role = db.Column(db.String(20), nullable=False, default='customer') # 'admin' or 'customer'
    pan_no = db.Column(db.String(20), nullable=True)
    ckyc_no = db.Column(db.String(30), nullable=True)
    akyc_no = db.Column(db.String(30), nullable=True)
    kyc_status = db.Column(db.String(20), nullable=True, default='Pending')
    cheque_book_applied = db.Column(db.Boolean, default=False)
    cheque_book_status = db.Column(db.String(30), nullable=True, default='Not Requested')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # type: ignore

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def verify_pin(self, pin_value):
        try:
            return self.pin == int(pin_value)
        except (ValueError, TypeError):
            return False


class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    account_number = db.Column(db.String(20), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False) # 'Deposit' or 'Withdraw'
    amount = db.Column(db.Float, nullable=False)
    balance_after_transaction = db.Column(db.Float, nullable=False)
    date_time = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # type: ignore


class Cheque(db.Model):
    __tablename__ = 'cheques'

    id = db.Column(db.Integer, primary_key=True)
    cheque_number = db.Column(db.String(30), unique=True, nullable=False)
    account_number = db.Column(db.String(20), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, default=0.0)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Unused')
    remarks = db.Column(db.String(200), nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # type: ignore


class OTP(db.Model):
    __tablename__ = 'otps'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    otp = db.Column(db.String(10), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    verified = db.Column(db.Boolean, default=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # type: ignore
