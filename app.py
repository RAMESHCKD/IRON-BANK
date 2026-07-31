from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from flask import Flask, redirect, url_for, session
from sqlalchemy import inspect, text
from config import Config
from models.db_models import db, User, Cheque

DISPLAY_TIMEZONE = ZoneInfo('Asia/Kolkata')


def local_datetime(value):
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(DISPLAY_TIMEZONE)

def ensure_user_profile_columns():
    inspector = inspect(db.engine)
    existing_columns = {column['name'] for column in inspector.get_columns('users')}
    with db.engine.begin() as connection:
        if 'pan_no' not in existing_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN pan_no VARCHAR(20)"))
        if 'ckyc_no' not in existing_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN ckyc_no VARCHAR(30)"))
        if 'akyc_no' not in existing_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN akyc_no VARCHAR(30)"))
        if 'kyc_status' not in existing_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN kyc_status VARCHAR(20) DEFAULT 'Pending'"))
        if 'cheque_book_applied' not in existing_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN cheque_book_applied BOOLEAN DEFAULT 0"))
        if 'cheque_book_status' not in existing_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN cheque_book_status VARCHAR(30) DEFAULT 'Not Requested'"))


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize DB
    db.init_app(app)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    
    # Root route
    @app.route('/')
    def index():
        if 'user_id' in session:
            if session.get('role') == 'admin':
                return redirect(url_for('admin.dashboard'))
            session.clear()
            flash("Customer access is no longer available.", "warning")
        return redirect(url_for('auth.login'))
        
    # Context processor for inject base variables if needed
    @app.context_processor
    def inject_now():
        return {'now': datetime.now(timezone.utc).astimezone(DISPLAY_TIMEZONE)}

    app.jinja_env.filters['local_datetime'] = local_datetime
        
    # Database seeding
    with app.app_context():
        db.create_all()
        ensure_user_profile_columns()
        
        # Seed default Admin
        admin_exists = User.query.filter_by(user_id='admin').first()
        if not admin_exists:
            admin_user = User(
                user_id='admin',
                name='System Administrator',
                email='cbs80200@gmail.com',
                role='admin'
            )
            admin_user.set_password('admin@2118')
            db.session.add(admin_user)
            print("Default Administrator created (UserID: admin)")
        else:
            admin_exists.email = 'cbs80200@gmail.com'
            admin_exists.set_password('admin@2118')
            
        # Seed default Customer
        customer_exists = User.query.filter_by(user_id='customer').first()
        if not customer_exists:
            customer_user = User(
                user_id='customer',
                account_number='100',
                name='John Doe',
                phone='9876543210',
                email='customer@ironbank.com',
                pin=1234,
                balance=5000.0,
                role='customer'
            )
            customer_user.set_password('customerpassword')
            db.session.add(customer_user)
            print("Default Customer created (UserID: customer, Password: customerpassword, PIN: 1234)")

        customer_user = User.query.filter_by(user_id='customer').first()
        if customer_user:
            sample_cheques = [
                ('CHQ-1001', 2500.0, 'Unused', 'Fresh cheque issued to customer'),
                ('CHQ-1002', 4000.0, 'Used', 'Cleared through account'),
                ('CHQ-1003', 1500.0, 'Passed', 'Cheque passed and cleared'),
                ('CHQ-1004', 3200.0, 'Blocked', 'Blocked by bank review')
            ]
            for cheque_number, amount, status, remarks in sample_cheques:
                existing = Cheque.query.filter_by(cheque_number=cheque_number).first()
                if not existing:
                    db.session.add(Cheque(
                        cheque_number=cheque_number,
                        account_number=customer_user.account_number,
                        customer_name=customer_user.name,
                        amount=amount,
                        status=status,
                        remarks=remarks
                    ))
            
        db.session.commit()
        
    return app

if __name__ == '__main__':
    app = create_app()
    # Run the server on localhost port 5000
    app.run(debug=True, host='127.0.0.1', port=5000)
