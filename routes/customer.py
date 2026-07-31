from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from models.db_models import db, User, Transaction

customer_bp = Blueprint('customer', __name__)

def customer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'customer':
            flash("Access denied. Customer account required.", "danger")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@customer_bp.route('/customer/dashboard')
@customer_required
def dashboard():
    user = User.query.filter_by(user_id=session['user_id']).first()
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
        
    recent_transactions = Transaction.query.filter_by(account_number=user.account_number)\
                                           .order_by(Transaction.date_time.desc())\
                                           .limit(5).all()
                                           
    return render_template('customer/dashboard.html', user=user, recent_transactions=recent_transactions)

@customer_bp.route('/customer/deposit')
@customer_required
def disabled_actions():
    flash("Deposit operations can only be performed by an Administrator.", "danger")
    return redirect(url_for('customer.dashboard'))

@customer_bp.route('/customer/withdraw', methods=['GET', 'POST'])
@customer_required
def withdraw():
    user = User.query.filter_by(user_id=session['user_id']).first()
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        amount_str = request.form.get('amount', '').strip()
        pin = request.form.get('pin', '').strip()
        withdrawal_method = request.form.get('withdrawal_method', 'Withdrawal Slip').strip()
        remarks = request.form.get('remarks', '').strip()

        if not amount_str or not pin:
            flash("Please enter an amount and your transaction PIN.", "danger")
            return render_template('customer/withdraw.html', user=user, withdrawal_method=withdrawal_method)

        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash("Invalid amount! Must be a positive decimal number.", "danger")
            return render_template('customer/withdraw.html', user=user, withdrawal_method=withdrawal_method)

        if amount > user.balance:
            flash("Insufficient balance for this withdrawal request.", "danger")
            return render_template('customer/withdraw.html', user=user, withdrawal_method=withdrawal_method)

        if not user.verify_pin(pin):
            flash("Incorrect transaction PIN.", "danger")
            return render_template('customer/withdraw.html', user=user, withdrawal_method=withdrawal_method)

        user.balance -= amount

        note = f"Withdraw via {withdrawal_method}"
        if remarks:
            note = f"{note} ({remarks})"

        new_tx = Transaction(
            account_number=user.account_number,
            transaction_type=note,
            amount=amount,
            balance_after_transaction=user.balance
        )
        db.session.add(new_tx)
        db.session.commit()

        flash(f"Successfully withdrew ₹{amount:,.2f} via {withdrawal_method}.", "success")
        return redirect(url_for('customer.dashboard'))

    return render_template('customer/withdraw.html', user=user)

@customer_bp.route('/customer/transfer', methods=['GET', 'POST'])
@customer_required
def transfer():
    user = User.query.filter_by(user_id=session['user_id']).first()
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        recipient_account = request.form.get('recipient_account', '').strip()
        amount_str = request.form.get('amount', '').strip()
        pin = request.form.get('pin', '').strip()
        
        if not recipient_account or not amount_str or not pin:
            flash("Please enter Recipient Account, Amount and transaction PIN.", "danger")
            return render_template('customer/transfer.html', user=user)
            
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash("Invalid amount! Must be a positive decimal number.", "danger")
            return render_template('customer/transfer.html', user=user)
            
        if amount > user.balance:
            flash("Insufficient balance for this transfer.", "danger")
            return render_template('customer/transfer.html', user=user)
            
        if recipient_account == user.account_number:
            flash("You cannot transfer money to your own account.", "danger")
            return render_template('customer/transfer.html', user=user)
            
        if not user.verify_pin(pin):
            flash("Incorrect transaction PIN.", "danger")
            return render_template('customer/transfer.html', user=user)
            
        recipient = User.query.filter_by(account_number=recipient_account, role='customer').first()
        if not recipient:
            flash("Recipient account not found. Please verify the account number.", "danger")
            return render_template('customer/transfer.html', user=user)
            
        # Process Transfer
        user.balance -= amount
        recipient.balance += amount
        
        # Log Sender Transaction
        sender_tx = Transaction(
            account_number=user.account_number,
            transaction_type=f'Transfer to {recipient.name} ({recipient.account_number})',
            amount=amount,
            balance_after_transaction=user.balance
        )
        # Log Recipient Transaction
        recipient_tx = Transaction(
            account_number=recipient.account_number,
            transaction_type=f'Transfer from {user.name} ({user.account_number})',
            amount=amount,
            balance_after_transaction=recipient.balance
        )
        
        db.session.add(sender_tx)
        db.session.add(recipient_tx)
        db.session.commit()
        
        flash(f"Successfully transferred ₹{amount:,.2f} to {recipient.name} (Acc: {recipient.account_number}).", "success")
        return redirect(url_for('customer.dashboard'))
        
    return render_template('customer/transfer.html', user=user)

@customer_bp.route('/customer/transactions')
@customer_required
def transactions():
    user = User.query.filter_by(user_id=session['user_id']).first()
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
        
    txs = Transaction.query.filter_by(account_number=user.account_number)\
                            .order_by(Transaction.date_time.desc()).all()
                            
    return render_template('customer/transactions.html', user=user, transactions=txs)

@customer_bp.route('/customer/settings', methods=['GET', 'POST'])
@customer_required
def settings():
    user = User.query.filter_by(user_id=session['user_id']).first()
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            phone = request.form.get('phone', '').strip()
            email = request.form.get('email', '').strip()
            address = request.form.get('address', '').strip()
            
            if not email or not phone:
                flash("Email and Phone number are required.", "danger")
                return render_template('customer/settings.html', user=user)
                
            # Verify email doesn't collide with another user
            existing_email = User.query.filter(User.email == email, User.id != user.id).first()
            if existing_email:
                flash("Email address is already registered to another account.", "danger")
                return render_template('customer/settings.html', user=user)
                
            user.phone = phone
            user.email = email
            user.address = address
            db.session.commit()
            
            # Update session variables if changed
            session['name'] = user.name
            
            flash("Profile details updated successfully.", "success")
            return redirect(url_for('customer.dashboard'))
            
        elif action == 'change_password':
            old_pass = request.form.get('old_password', '')
            new_pass = request.form.get('new_password', '')
            confirm_pass = request.form.get('confirm_password', '')
            
            if not (old_pass and new_pass and confirm_pass):
                flash("Please fill in all password fields.", "danger")
                return render_template('customer/settings.html', user=user)
                
            if not user.check_password(old_pass):
                flash("Incorrect current password.", "danger")
                return render_template('customer/settings.html', user=user)
                
            if new_pass != confirm_pass:
                flash("New passwords do not match.", "danger")
                return render_template('customer/settings.html', user=user)
                
            if len(new_pass) < 6:
                flash("Password must be at least 6 characters long.", "danger")
                return render_template('customer/settings.html', user=user)
                
            user.set_password(new_pass)
            db.session.commit()
            
            flash("Password changed successfully.", "success")
            return redirect(url_for('customer.dashboard'))
            
    return render_template('customer/settings.html', user=user)
