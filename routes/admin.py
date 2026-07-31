import random
import re
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, session, flash, jsonify
from models.db_models import db, User, Transaction, Cheque


def find_customer_by_lookup(identifier):
    if not identifier:
        return None
    lookup_value = identifier.strip()
    return User.query.filter(
        (User.account_number == lookup_value) | (User.user_id == lookup_value),
        User.role == 'customer'
    ).first()

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash("Access denied. Administrator privileges required.", "danger")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def generate_account_number():
    """Generates a unique 3-digit account number as per the original CLI script requirement."""
    while True:
        acc_num = str(random.randint(100, 999))
        existing = User.query.filter_by(account_number=acc_num).first()
        if not existing:
            return acc_num


def find_cheque_by_number(cheque_number):
    if not cheque_number:
        return None
    lookup_value = cheque_number.strip()
    return Cheque.query.filter_by(cheque_number=lookup_value).first()

@admin_bp.route('/admin/dashboard')
@admin_required
def dashboard():
    total_customers = User.query.filter_by(role='customer').count()
    all_customers = User.query.filter_by(role='customer').all()

    current_account_total = sum(
        c.balance for c in all_customers
        if c.account_number and c.account_number.isdigit() and int(c.account_number) % 2 == 0
    )
    savings_account_total = sum(
        c.balance for c in all_customers
        if c.account_number and c.account_number.isdigit() and int(c.account_number) % 2 != 0
    )

    total_transactions_count = Transaction.query.count()
    recent_transactions = Transaction.query.order_by(Transaction.date_time.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
                           total_customers=total_customers,
                           current_account_total=current_account_total,
                           savings_account_total=savings_account_total,
                           total_transactions=total_transactions_count,
                           recent_transactions=recent_transactions)


@admin_bp.route('/admin/customers', methods=['GET', 'POST'])
@admin_required
def customers():
    post_action = None
    if request.method == 'POST':
        action = request.form.get('action')
        post_action = action
        account_number = request.form.get('account_number', '').strip()
        cheque_number = request.form.get('cheque_number', '').strip()

        if action == 'lookup_customer':
            customer = find_customer_by_lookup(account_number)
            if customer:
                return redirect(url_for('admin.customers', account_number=customer.account_number, lookup='1'))
            flash(f"Customer '{account_number}' was not found.", "danger")
            return redirect(url_for('admin.customers'))

        if action == 'lookup_cheque':
            cheque = find_cheque_by_number(cheque_number)
            if cheque:
                return redirect(url_for('admin.customers', account_number=cheque.account_number, lookup='1', cheque_number=cheque.cheque_number, active_tab='cheque'))
            flash(f"Cheque '{cheque_number}' was not found.", "danger")
            return redirect(url_for('admin.customers', account_number=account_number or ''))

        if action == 'apply_cheque':
            customer = User.query.filter_by(account_number=account_number, role='customer').first()
            if customer:
                customer.cheque_book_applied = True
                customer.cheque_book_status = 'Requested'
                db.session.commit()
                flash(f"Cheque book request submitted for {customer.name}.", "success")
            else:
                flash("Customer not found.", "danger")
            # Continue to the normal render below so the customer profile stays in place.

        if action == 'stop_cheque':
            customer = User.query.filter_by(account_number=account_number, role='customer').first()
            if customer:
                customer.cheque_book_applied = False
                customer.cheque_book_status = 'Not Requested'
                db.session.commit()
                flash(f"Cheque book request stopped for {customer.name}.", "success")
            else:
                flash("Customer not found.", "danger")
            # Continue to the normal render below so the customer profile stays in place.

        if action == 'update_kyc':
            customer = User.query.filter_by(account_number=account_number, role='customer').first()
            if customer:
                pan_number = request.form.get('pan_no', '').strip().upper()
                pan_editable = customer.kyc_status == 'Rejected'
                if customer.pan_no and not pan_editable and pan_number != customer.pan_no:
                    flash("PAN number cannot be changed after it has been submitted.", "danger")
                elif (not customer.pan_no or pan_editable) and not re.fullmatch(r'[A-Z]{5}[0-9]{4}[A-Z]', pan_number):
                    flash("Enter a valid PAN number in the format ABCDE1234F.", "danger")
                else:
                    customer.kyc_status = request.form.get('kyc_status', 'Pending').strip() or 'Pending'
                    if not customer.akyc_no:
                        customer.akyc_no = f"AKYC-{customer.account_number}"
                    if not customer.ckyc_no:
                        customer.ckyc_no = f"CKYC-{customer.account_number}"
                    if not customer.pan_no or pan_editable:
                        customer.pan_no = pan_number
                    db.session.commit()
                    flash("KYC details updated successfully.", "success")
            else:
                flash("Customer not found.", "danger")
            # Continue to the normal render below so the KYC tab stays open.

        if action in {'mark_cheque_passed', 'block_cheque'}:
            cheque = find_cheque_by_number(cheque_number)
            if cheque:
                if action == 'mark_cheque_passed':
                    cheque.status = 'Passed'
                    flash(f"Cheque {cheque.cheque_number} marked as Passed.", "success")
                elif action == 'block_cheque':
                    cheque.status = 'Blocked'
                    flash(f"Cheque {cheque.cheque_number} blocked successfully.", "warning")
                db.session.commit()
            else:
                flash("Cheque not found.", "danger")
            return redirect(url_for('admin.customers', account_number=account_number, lookup='1', cheque_number=cheque_number, active_tab='cheque'))

    total_customers = User.query.filter_by(role='customer').count()
    all_customers = User.query.filter_by(role='customer').all()

    current_account_total = sum(
        c.balance for c in all_customers
        if c.account_number and c.account_number.isdigit() and int(c.account_number) % 2 == 0
    )
    savings_account_total = sum(
        c.balance for c in all_customers
        if c.account_number and c.account_number.isdigit() and int(c.account_number) % 2 != 0
    )

    recent_transactions = Transaction.query.order_by(Transaction.date_time.desc()).limit(5).all()
    is_inline_profile_action = post_action in {'apply_cheque', 'stop_cheque', 'update_kyc'}
    selected_account = request.args.get('account_number', '').strip() or (account_number if is_inline_profile_action else '')
    cheque_number = request.args.get('cheque_number', '').strip()
    default_tab = 'kyc' if post_action == 'update_kyc' else 'cheque' if post_action in {'apply_cheque', 'stop_cheque'} else 'summary'
    active_tab = request.args.get('active_tab', default_tab)
    lookup_performed = request.args.get('lookup') == '1' or is_inline_profile_action
    pan_input = request.form.get('pan_no', '').strip().upper() if post_action == 'update_kyc' else ''
    selected_customer = find_customer_by_lookup(selected_account) if lookup_performed and selected_account else None
    selected_cheque = find_cheque_by_number(cheque_number) if cheque_number else None
    if selected_cheque and selected_customer and selected_cheque.account_number != selected_customer.account_number:
        selected_cheque = None
    customer_transactions = []
    if selected_customer:
        customer_transactions = Transaction.query.filter_by(account_number=selected_customer.account_number).order_by(Transaction.date_time.desc()).all()

    return render_template('admin/customers.html',
                           customers=all_customers,
                           total_customers=total_customers,
                           current_account_total=current_account_total,
                           savings_account_total=savings_account_total,
                           total_transactions=Transaction.query.count(),
                           recent_transactions=recent_transactions,
                           selected_customer=selected_customer,
                           customer_transactions=customer_transactions,
                           selected_account=selected_account,
                           selected_cheque=selected_cheque,
                           cheque_number=cheque_number,
                           active_tab=active_tab,
                           pan_input=pan_input)

@admin_bp.route('/admin/add-customer', methods=['GET', 'POST'])
@admin_required
def add_customer():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        pan_number = request.form.get('pan_no', '').strip().upper()
        
        # Simple validations
        if not (name and phone and email and address and pan_number):
            flash("Name, Phone, Email, Address, and PAN are required.", "danger")
            return render_template('admin/add_customer.html')

        if not re.fullmatch(r"[A-Za-z][A-Za-z .'-]{1,99}", name):
            flash("Enter a valid name using letters, spaces, apostrophes, or hyphens.", "danger")
            return render_template('admin/add_customer.html')

        if not re.fullmatch(r"[6-9][0-9]{9}", phone):
            flash("Enter a valid 10-digit mobile number starting with 6, 7, 8, or 9.", "danger")
            return render_template('admin/add_customer.html')

        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]{2,}", email):
            flash("Enter a valid email address.", "danger")
            return render_template('admin/add_customer.html')

        if len(address) < 5 or len(address) > 200:
            flash("Address must contain between 5 and 200 characters.", "danger")
            return render_template('admin/add_customer.html')

        if not re.fullmatch(r'[A-Z]{5}[0-9]{4}[A-Z]', pan_number):
            flash("Enter a valid PAN number in the format ABCDE1234F.", "danger")
            return render_template('admin/add_customer.html')
            
        if User.query.filter_by(email=email).first():
            flash("Email address already registered.", "danger")
            return render_template('admin/add_customer.html')
            
        # Create user
        account_no = generate_account_number()
        internal_user_id = f"customer{account_no}"
        new_customer = User(
            user_id=internal_user_id,
            account_number=account_no,
            name=name,
            phone=phone,
            email=email,
            address=address,
            pan_no=pan_number,
            pin=random.randint(1000, 9999),
            balance=0.0,
            role='customer'
        )
        new_customer.set_password(random.randbytes(16).hex())
        
        db.session.add(new_customer)
        db.session.commit()
        
        flash(f"Customer Account created successfully! Account No: {account_no}", "success")
        return redirect(url_for('admin.dashboard'))
        
    return render_template('admin/add_customer.html')

@admin_bp.route('/admin/deposit', methods=['GET', 'POST'])
@admin_required
def deposit():
    selected_method = 'Cash'
    prefill_acc = ''
    show_details = False
    show_deposit_form = True
    deposit_account_number = None
    deposit_account_name = None
    deposit_account_balance = None
    cheque_date = ''
    cheque_no = ''

    if request.method == 'POST':
        selected_method = request.form.get('deposit_method', 'Cash')
        account_number = request.form.get('account_number', '').strip()
        amount_str = request.form.get('amount', '').strip()
        cheque_date = request.form.get('cheque_date', '').strip()
        cheque_no = request.form.get('cheque_no', '').strip()
        
        if not account_number or not amount_str:
            flash("Please enter both Account Number and Amount.", "danger")
            return render_template(
                'admin/deposit.html',
                prefill_acc=account_number,
                selected_method=selected_method,
                show_details=False,
                deposit_account_number=account_number,
                deposit_account_name=None,
                deposit_account_balance=None,
                cheque_date=cheque_date,
                cheque_no=cheque_no
            )
            
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash("Invalid amount! Must be a positive decimal number.", "danger")
            return render_template(
                'admin/deposit.html',
                prefill_acc=account_number,
                selected_method=selected_method,
                show_details=False,
                deposit_account_number=account_number,
                deposit_account_name=None,
                deposit_account_balance=None,
                cheque_date=cheque_date,
                cheque_no=cheque_no,
                show_deposit_form=show_deposit_form
            )
            
        customer = User.query.filter_by(account_number=account_number, role='customer').first()
        if not customer:
            flash(f"Account Number {account_number} not found.", "danger")
            return render_template(
                'admin/deposit.html',
                prefill_acc=account_number,
                selected_method=selected_method,
                show_details=False,
                deposit_account_number=account_number,
                deposit_account_name=None,
                deposit_account_balance=None,
                cheque_date=cheque_date,
                cheque_no=cheque_no,
                show_deposit_form=show_deposit_form
            )

        if selected_method == 'Cheque' and (not cheque_date or not cheque_no):
            flash("Please enter the cheque date and cheque number for cheque deposits.", "danger")
            return render_template(
                'admin/deposit.html',
                prefill_acc=account_number,
                selected_method=selected_method,
                show_details=True,
                deposit_account_number=account_number,
                deposit_account_name=customer.name,
                deposit_account_balance=customer.balance,
                cheque_date=cheque_date,
                cheque_no=cheque_no,
                show_deposit_form=True
            )
            
        # Process Deposit
        customer.balance += amount
        
        # Log Transaction
        new_tx = Transaction(
            account_number=customer.account_number,
            transaction_type='Cheque Deposit' if selected_method == 'Cheque' else 'Deposit',
            amount=amount,
            balance_after_transaction=customer.balance
        )
        db.session.add(new_tx)
        db.session.commit()
        
        if selected_method == 'Cheque':
            flash(f"₹{amount:,.2f} deposited successfully to Account No: {account_number} ({customer.name}) via Cheque (Date: {cheque_date}, No: {cheque_no}).", "success")
        else:
            flash(f"₹{amount:,.2f} deposited successfully to Account No: {account_number} ({customer.name}) via Cash.", "success")
        show_details = True
        show_deposit_form = False
        prefill_acc = account_number
        deposit_account_number = prefill_acc
        deposit_account_name = customer.name
        deposit_account_balance = customer.balance
        return render_template(
            'admin/deposit.html',
            prefill_acc=prefill_acc,
            selected_method=selected_method,
            show_details=show_details,
            deposit_account_number=deposit_account_number,
            deposit_account_name=deposit_account_name,
            deposit_account_balance=deposit_account_balance,
            cheque_date=cheque_date,
            cheque_no=cheque_no,
            show_deposit_form=show_deposit_form
        )
        
    # Optional pre-filled account number from dashboard URL
    prefill_acc = request.args.get('acc_no', '')
    return render_template(
        'admin/deposit.html',
        prefill_acc=prefill_acc,
        selected_method=selected_method,
        show_details=False,
        deposit_account_number=prefill_acc if prefill_acc else None,
        deposit_account_name=None,
        deposit_account_balance=None,
        cheque_date='',
        cheque_no='',
        show_deposit_form=show_deposit_form
    )

@admin_bp.route('/admin/edit-customer/<int:customer_id>', methods=['GET', 'POST'])
@admin_required
def edit_customer(customer_id):
    customer = User.query.filter_by(id=customer_id, role='customer').first_or_404()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        user_id = request.form.get('user_id', '').strip()
        pin = request.form.get('pin', '').strip()

        if not (name and email and user_id and pin):
            flash("Name, Email, User ID, and PIN are required.", "danger")
            return render_template('admin/edit_customer.html', customer=customer)

        try:
            pin_val = int(pin)
            if len(pin) != 4:
                raise ValueError
        except ValueError:
            flash("PIN must be a 4-digit number.", "danger")
            return render_template('admin/edit_customer.html', customer=customer)

        duplicate_user = User.query.filter(User.id != customer.id, User.user_id == user_id).first()
        if duplicate_user:
            flash("User ID already exists.", "danger")
            return render_template('admin/edit_customer.html', customer=customer)

        duplicate_email = User.query.filter(User.id != customer.id, User.email == email).first()
        if duplicate_email:
            flash("Email address already registered.", "danger")
            return render_template('admin/edit_customer.html', customer=customer)

        customer.name = name
        customer.phone = phone
        customer.email = email
        customer.address = address
        customer.user_id = user_id
        customer.pin = pin_val

        db.session.commit()
        flash("Customer details updated successfully.", "success")
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/edit_customer.html', customer=customer)

@admin_bp.route('/admin/account-info/<account_number>')
@admin_required
def account_info(account_number):
    customer = User.query.filter_by(account_number=account_number, role='customer').first()
    if not customer:
        return jsonify({'error': 'Account not found'}), 404

    return jsonify({
        'name': customer.name,
        'balance': round(customer.balance, 2)
    })

@admin_bp.route('/admin/transactions')
@admin_required
def audit_transactions():
    transactions = Transaction.query.order_by(Transaction.date_time.desc()).all()
    # Map account numbers to names for user friendly display
    cust_map = {c.account_number: c.name for c in User.query.filter_by(role='customer').all()}
    return render_template('admin/transactions.html', transactions=transactions, cust_map=cust_map)

@admin_bp.route('/admin/clear-logs', methods=['POST'])
@admin_required
def clear_logs():
    try:
        # Delete all records from Transaction table
        num_deleted = db.session.query(Transaction).delete()
        db.session.commit()
        flash(f"System audit logs cleared successfully! {num_deleted} entries removed.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Failed to clear system audit logs.", "danger")
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/withdraw', methods=['GET', 'POST'])
@admin_required
def withdraw():
    if request.method == 'POST':
        account_number = request.form.get('account_number', '').strip()
        amount_str = request.form.get('amount', '').strip()
        
        if not account_number or not amount_str:
            flash("Please enter both Account Number and Amount.", "danger")
            return render_template('admin/withdraw.html')
            
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash("Invalid amount! Must be a positive decimal number.", "danger")
            return render_template('admin/withdraw.html')
            
        customer = User.query.filter_by(account_number=account_number, role='customer').first()
        if not customer:
            flash(f"Account Number {account_number} not found.", "danger")
            return render_template('admin/withdraw.html')
            
        if amount > customer.balance:
            flash(f"Insufficient balance in Account No: {account_number} ({customer.name}). Current balance: ₹{customer.balance:,.2f}", "danger")
            return render_template('admin/withdraw.html', prefill_acc=account_number)
            
        # Process Withdraw
        customer.balance -= amount
        
        # Log Transaction
        new_tx = Transaction(
            account_number=customer.account_number,
            transaction_type='Withdraw',
            amount=amount,
            balance_after_transaction=customer.balance
        )
        db.session.add(new_tx)
        db.session.commit()
        
        flash(f"₹{amount:,.2f} withdrawn successfully from Account No: {account_number} ({customer.name}).", "success")
        return redirect(url_for('admin.dashboard'))
        
    # Optional pre-filled account number from dashboard URL
    prefill_acc = request.args.get('acc_no', '')
    return render_template('admin/withdraw.html', prefill_acc=prefill_acc)
