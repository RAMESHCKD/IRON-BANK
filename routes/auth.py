import random
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, render_template, redirect, url_for, request, session, flash, current_app
from models.db_models import db, User, OTP

auth_bp = Blueprint('auth', __name__)

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(to_email, otp_code):
    """
    Sends OTP code to target email using SMTP.
    Falls back to console output if SMTP credentials are missing or fail.
    Returns: (success_bool, message)
    """
    mail_username = current_app.config.get('MAIL_USERNAME', '')
    mail_password = current_app.config.get('MAIL_PASSWORD', '')
    mail_server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
    mail_port = current_app.config.get('MAIL_PORT', 587)
    
    # Check if config exists
    if not mail_username or not mail_password:
        return False, "OTP email service is not configured. Contact the administrator."
    
    try:
        msg = MIMEMultipart()
        msg['From'] = mail_username
        msg['To'] = to_email
        msg['Subject'] = f"IronBank - Security Verification OTP: {otp_code}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f6f9; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 8px; border: 1px solid #e1e8ed; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);">
                <div style="text-align: center; border-bottom: 2px solid #003366; padding-bottom: 20px; margin-bottom: 20px;">
                    <h2 style="color: #003366; margin: 0;">🏦 IRONBANK</h2>
                    <p style="color: #667788; margin: 5px 0 0 0; font-size: 14px;">Secure Online Banking Portal</p>
                </div>
                <div style="padding: 10px 0;">
                    <p style="font-size: 16px; color: #333333;">Dear Customer,</p>
                    <p style="font-size: 16px; color: #555555; line-height: 1.5;">
                        You have initiated a login request to your IronBank account. Please use the following 6-digit One-Time Password (OTP) to complete your authentication. This OTP is valid for 5 minutes.
                    </p>
                    <div style="text-align: center; margin: 30px 0;">
                        <span style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #003366; background-color: #f0f4f8; padding: 15px 30px; border-radius: 6px; border: 1px dashed #003366; display: inline-block;">
                            {otp_code}
                        </span>
                    </div>
                    <p style="font-size: 14px; color: #ff3333; font-weight: bold;">
                        If you did not initiate this request, please change your password immediately or contact IronBank Customer Support.
                    </p>
                </div>
                <div style="border-top: 1px solid #e1e8ed; padding-top: 20px; margin-top: 30px; text-align: center; font-size: 12px; color: #8899aa;">
                    This is an automated system email. Please do not reply directly.
                    <br>IronBank Banking Corporation &copy; 2026. All rights reserved.
                </div>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(mail_server, mail_port)
        server.starttls()
        server.login(mail_username, mail_password)
        server.sendmail(mail_username, to_email, msg.as_string())
        server.quit()
        return True, "OTP has been sent to your registered email address."
    except Exception as e:
        print(f"\n[ERROR sending OTP email] {e}")
        return False, "OTP email delivery failed. Please try again later."

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, redirect based on role
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        session.clear()
            
    if request.method == 'POST':
        user_id = request.form.get('user_id', '').strip()
        password = request.form.get('password', '')
        
        if not user_id or not password:
            flash("Please enter both User ID and Password.", "danger")
            return render_template('login.html')
            
        user = User.query.filter_by(user_id=user_id).first()
        
        if user and user.check_password(password):
            if user.role != 'admin':
                flash("Customer login is no longer available.", "danger")
                return render_template('login.html')

            # Password verified, now generate and send OTP
            otp_code = generate_otp()
            expires_at = datetime.utcnow() + timedelta(minutes=5)
            
            # Save OTP to database
            new_otp = OTP(email=user.email, otp=otp_code, expires_at=expires_at, verified=False)
            db.session.add(new_otp)
            db.session.commit()
            
            # Send OTP email
            success, msg = send_otp_email(user.email, otp_code)
            
            # Setup pending session
            session['pending_user_id'] = user.user_id
            session['pending_otp_email'] = user.email
            
            if success:
                flash(msg, "success")
            else:
                # Store the fallback warning for presentation
                flash(msg, "warning")
                
            return redirect(url_for('auth.verify_otp'))
        else:
            flash("Invalid User ID or Password.", "danger")
            
    return render_template('login.html')

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    # Must have password-verified user in pending session
    if 'pending_user_id' not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for('auth.login'))
        
    pending_user_id = session['pending_user_id']
    pending_email = session['pending_otp_email']
    user = User.query.filter_by(user_id=pending_user_id).first()
    
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        otp_input = request.form.get('otp', '').strip()
        
        if not otp_input:
            flash("Please enter the 6-digit OTP code.", "danger")
            return render_template('otp.html', email=pending_email)
            
        # Get active unverified OTPs for this email, sorted by expiry descending
        otp_records = OTP.query.filter_by(email=user.email, verified=False).order_by(OTP.expires_at.desc()).all()
        
        valid_otp = False
        for record in otp_records:
            # Check expiration
            if record.expires_at > datetime.utcnow():
                if record.otp == otp_input:
                    record.verified = True
                    db.session.commit()
                    valid_otp = True
                    break
            else:
                # Expired OTP, let's delete or skip
                pass
                
        if valid_otp:
            # Success! Elevate session
            session.pop('pending_user_id', None)
            session.pop('pending_otp_email', None)
            
            session['user_id'] = user.user_id
            session['role'] = user.role
            session['name'] = user.name
                
            flash(f"Welcome back, {user.name}!", "success")
            
            return redirect(url_for('admin.dashboard'))
        else:
            flash("Invalid or expired OTP. Please try again.", "danger")
            
    return render_template('otp.html', email=pending_email)

@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    if 'pending_user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user = User.query.filter_by(user_id=session['pending_user_id']).first()
    if not user:
        return redirect(url_for('auth.login'))
        
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    new_otp = OTP(email=user.email, otp=otp_code, expires_at=expires_at, verified=False)
    db.session.add(new_otp)
    db.session.commit()
    
    success, msg = send_otp_email(user.email, otp_code)
    
    if success:
        flash("A new OTP has been sent to your email.", "success")
    else:
        flash(msg, "warning")
        
    return redirect(url_for('auth.verify_otp'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('auth.login'))
