// IronBank Client-Side JavaScript Utilities

document.addEventListener('DOMContentLoaded', () => {
    // 0. Mobile Navigation Menu Toggle
    const navToggle = document.getElementById('navToggle');
    const navLinks = document.getElementById('navLinks');
    if (navToggle && navLinks) {
        navToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            navLinks.classList.toggle('active');
            
            // Toggle hamburger icon between bars and close icon
            const icon = navToggle.querySelector('i');
            if (icon) {
                if (navLinks.classList.contains('active')) {
                    icon.classList.remove('fa-bars');
                    icon.classList.add('fa-xmark');
                } else {
                    icon.classList.remove('fa-xmark');
                    icon.classList.add('fa-bars');
                }
            }
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (navLinks.classList.contains('active') && !navLinks.contains(e.target) && !navToggle.contains(e.target)) {
                navLinks.classList.remove('active');
                const icon = navToggle.querySelector('i');
                if (icon) {
                    icon.classList.remove('fa-xmark');
                    icon.classList.add('fa-bars');
                }
            }
        });
    }

    // 1. Toggle method tabs for withdrawals and deposits
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => {
            const method = button.dataset.method || 'Withdrawal Slip';
            document.querySelectorAll('.tab-button').forEach(item => item.classList.remove('active'));
            document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));
            button.classList.add('active');
            const targetPanel = document.getElementById(`tab-${button.dataset.tab}`);
            if (targetPanel) {
                targetPanel.classList.add('active');
            }
            const hiddenInputId = button.dataset.input || 'withdrawal_method';
            const hiddenInput = document.getElementById(hiddenInputId);
            if (hiddenInput) {
                hiddenInput.value = method;
            }
        });
    });

    // 1a. Admin account lookup before withdrawal options appear
    const adminLookupButton = document.getElementById('admin-account-lookup');
    const adminAccountField = document.getElementById('account_number');
    const adminLookupStatus = document.getElementById('admin-lookup-status');
    const adminWithdrawDetails = document.getElementById('admin-withdraw-details');
    const accountNameDisplay = document.getElementById('admin-account-name');
    const accountNumberDisplay = document.getElementById('admin-account-number-display');
    const accountBalanceDisplay = document.getElementById('admin-account-balance');
    const amountField = document.getElementById('amount');

    if (adminLookupButton && adminAccountField && adminLookupStatus && adminWithdrawDetails) {
        const setLookupState = (message, isError = true) => {
            adminLookupStatus.textContent = message;
            adminLookupStatus.style.color = isError ? 'var(--danger)' : 'var(--success)';
            adminLookupStatus.style.display = 'block';
        };

        const clearLookupState = () => {
            adminLookupStatus.textContent = '';
            adminLookupStatus.style.display = 'none';
        };

        const showWithdrawDetails = (data) => {
            accountNumberDisplay.textContent = data.account_number || adminAccountField.value;
            accountNameDisplay.textContent = data.name || '-';
            accountBalanceDisplay.textContent = Number(data.balance).toFixed(2);
            adminWithdrawDetails.classList.remove('hidden');
        };

        const fetchAccountInfo = (accountNumber) => {
            if (!accountNumber) {
                setLookupState('Please enter a valid account number.');
                return;
            }

            clearLookupState();
            fetch(`/admin/account-info/${encodeURIComponent(accountNumber)}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Account not found');
                    }
                    return response.json();
                })
                .then(data => {
                    showWithdrawDetails(data);
                    clearLookupState();
                })
                .catch(() => {
                    adminWithdrawDetails.classList.add('hidden');
                    setLookupState(`Account ${accountNumber} not found.`, true);
                });
        };

        adminLookupButton.addEventListener('click', () => {
            fetchAccountInfo(adminAccountField.value.trim());
        });

        if (adminAccountField.value.trim()) {
            fetchAccountInfo(adminAccountField.value.trim());
        }
    }

    // 1b. Admin deposit account lookup before deposit details are enabled
    const depositLookupButton = document.getElementById('deposit-account-lookup');
    const depositAccountField = document.getElementById('account_number');
    const depositLookupStatus = document.getElementById('deposit-lookup-status');
    const depositAccountDetails = document.getElementById('deposit-account-details');
    const depositActionPanel = document.getElementById('deposit-action-panel');
    const depositNameDisplay = document.getElementById('deposit-account-name');
    const depositNumberDisplay = document.getElementById('deposit-account-number-display');
    const depositBalanceDisplay = document.getElementById('deposit-account-balance');
    const depositSubmit = document.getElementById('deposit-submit');
    const depositAmountField = document.getElementById('amount');

    if (depositLookupButton && depositAccountField && depositLookupStatus && depositAccountDetails && depositSubmit && depositAmountField && depositActionPanel) {
        const setDepositState = (message, isError = true) => {
            depositLookupStatus.textContent = message;
            depositLookupStatus.style.color = isError ? 'var(--danger)' : 'var(--success)';
            depositLookupStatus.style.display = 'block';
        };

        const clearDepositState = () => {
            depositLookupStatus.textContent = '';
            depositLookupStatus.style.display = 'none';
        };

        const showDepositDetails = (data) => {
            depositNumberDisplay.textContent = data.account_number || depositAccountField.value;
            depositNameDisplay.textContent = data.name || '-';
            depositBalanceDisplay.textContent = Number(data.balance).toFixed(2);
            depositAccountDetails.classList.remove('hidden');
            depositActionPanel.classList.remove('hidden');
            depositAmountField.disabled = false;
            depositSubmit.classList.remove('hidden');
        };

        const resetDepositFields = () => {
            depositAccountDetails.classList.add('hidden');
            depositActionPanel.classList.add('hidden');
            depositAmountField.disabled = true;
            depositSubmit.classList.add('hidden');
        };

        const fetchDepositAccountInfo = (accountNumber) => {
            if (!accountNumber) {
                setDepositState('Please enter a valid account number.');
                return;
            }

            clearDepositState();
            fetch(`/admin/account-info/${encodeURIComponent(accountNumber)}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Account not found');
                    }
                    return response.json();
                })
                .then(data => {
                    showDepositDetails(data);
                    clearDepositState();
                })
                .catch(() => {
                    resetDepositFields();
                    setDepositState(`Account ${accountNumber} not found.`, true);
                });
        };

        depositLookupButton.addEventListener('click', () => {
            fetchDepositAccountInfo(depositAccountField.value.trim());
        });

        if (depositAccountField.value.trim() && depositAccountDetails.classList.contains('hidden')) {
            resetDepositFields();
        }
    }

    // 2. Toast timer - dismiss OTP warning toast automatically after 15 seconds
    const demoToast = document.getElementById('otpDemoToast');
    if (demoToast) {
        setTimeout(() => {
            demoToast.style.transition = 'opacity 1s ease-out, transform 1s ease-out';
            demoToast.style.opacity = '0';
            demoToast.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                demoToast.remove();
            }, 1000);
        }, 15000);
    }

    // 3. Client Side numeric enforcement for banking forms
    const numericInputs = document.querySelectorAll('input[type="number"], .numeric-only');
    numericInputs.forEach(input => {
        input.addEventListener('keypress', (e) => {
            // Prevent non-numeric entries (allow dots only for floats if not specifically PIN)
            const isPin = input.id === 'pin' || input.name === 'pin' || input.dataset.pin === 'true';
            if (isPin) {
                if (!/[0-9]/.test(e.key)) {
                    e.preventDefault();
                }
            } else {
                if (!/[0-9.]/.test(e.key)) {
                    e.preventDefault();
                }
            }
        });
    });

    // 4. Dynamic alert fadeouts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        // Double click to dismiss alert quickly
        alert.addEventListener('dblclick', () => {
            alert.style.display = 'none';
        });
        
        // Auto fade out after 8 seconds
        setTimeout(() => {
            alert.style.transition = 'opacity 0.8s ease-out';
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 800);
        }, 8000);
    });

    // 5. Form Submit Protection Double Clicks
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', () => {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.dataset.originalText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing Request...';
                // Fallback in case of form error/no page reload
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = submitBtn.dataset.originalText;
                }, 4000);
            }
        });
    });
});
