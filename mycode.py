import random


# ---------------------- Account Class ---------------------- #
class Account:
    def __init__(self, account_no, holder_name, pin, balance=0):
        self.account_no = account_no
        self.holder_name = holder_name
        self.pin = pin
        self.balance = balance

    def deposit(self, amount):
        if amount <= 0:
            print("Invalid amount!")
        else:
            self.balance += amount
            print(f"₹{amount} deposited successfully.")
            print(f"Current Balance : ₹{self.balance}")

    def withdraw(self, amount):
        if amount <= 0:
            print("Invalid amount!")

        elif amount > self.balance:
            print("Insufficient Balance!")

        else:
            self.balance -= amount
            print(f"₹{amount} withdrawn successfully.")
            print(f"Current Balance : ₹{self.balance}")

    def checkbalance(self):
        print(f"Current Balance : ₹{self.balance}")

    def verifypin(self, pin):
        return self.pin == pin

    def getaccount_no(self):
        return self.account_no

    def getholder_name(self):
        return self.holder_name


# ---------------------- Customer Class ---------------------- #
class Customer:
    def __init__(self, name, phone, account):
        self.name = name
        self.phone = phone
        self.account = account

    def display(self):
        print("\nCustomer Details")
        print("---------------------------")
        print("Name :", self.name)
        print("Phone:", self.phone)
        print("Account No:", self.account.getaccount_no())


# ---------------------- Bank Class ---------------------- #
class Bank:
    def __init__(self):
        self.customers = {}

    def create_account(self):
        print("\n===== Create Account =====")

        name = input("Enter Name : ")
        phone = int(input("Enter Phone : "))
        pin = int(input("Create 4-digit PIN : "))

        account_no = random.randint(100, 999)

        account = Account(account_no, name, pin)
        customer = Customer(name, phone, account)

        self.customers[account_no] = customer

        print("\nAccount Created Successfully!")
        print("Your Account Number:", account_no)

    def login(self):
        print("\n===== Login =====")

        try:
            account_no = int(input("Account Number : "))
        except ValueError:
            print("Invalid Account Number!")
            return None

        pin = int(input("PIN : "))

        customer = self.customers.get(account_no)

        if customer and customer.account.verifypin(pin):
            print(f"\nWelcome {customer.name}")
            return customer.account

        print("Invalid Account Number or PIN!")
        return None


# ---------------------- CLI ---------------------- #
class BankingApplication:
    def __init__(self):
        self.bank = Bank()

    def account_menu(self, account):
        while True:
            print("\n====== ACCOUNT MENU ======")
            print("1. Deposit")
            print("2. Withdraw")
            print("3. Check Balance")
            print("4. Logout")

            choice = input("Enter Choice : ")

            if choice == "1":
                amount = float(input("Amount : "))
                account.deposit(amount)

            elif choice == "2":
                amount = float(input("Amount : "))
                account.withdraw(amount)

            elif choice == "3":
                account.checkbalance()

            elif choice == "4":
                print("Logged Out Successfully.")
                break

            else:
                print("Invalid Choice!")

    def run(self):
        while True:
            print("\n==============================")
            print("   **BANKING APPLICATION**  ")
            print("==============================")
            print("1. Create Account")
            print("2. Login")
            print("3. Exit")

            choice = input("Enter Choice : ")

            if choice == "1":
                self.bank.create_account()

            elif choice == "2":
                account = self.bank.login()

                if account:
                    self.account_menu(account)

            elif choice == "3":
                print("Thank You!")
                break

            else:
                print("Invalid Choice!")


# ---------------------- Main ---------------------- #
if __name__ == "__main__":
    app = BankingApplication()
    app.run()