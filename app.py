import csv
import os
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL
from functions import login_required, transacition_list_finder
from currency_converter import CurrencyConverter

# Global vars
c = CurrencyConverter()
currencies = c.currencies
# Configure application
app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def home():
    # 
    user_id = session["user_id"]
    finance = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget user
    session.clear()

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        # Make sure email submitted
        if not request.form.get("email"):
            return render_template("apology.html", msg="Please enter email")

        # Make sure password submitted
        elif not request.form.get("password"):
            flash("Error")
            return render_template("apology.html", msg="Please enter password")

        # Look for email
        rows = db.execute("SELECT * FROM users WHERE email = ?", email)
        # Ensure email exists and password is correct
        if len(rows)!= 1 or not check_password_hash(rows[0]["password"], password):
            return render_template("apology.html",  msg ="Invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Go to home page
        return redirect("/")

    else:
        return render_template("login.html")
    
###
@app.route("/logout")
def logout():
    # Forget user
    session.clear()

    # Go to login form
    return redirect("/login")

###
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        currency = request.form.get("currency").upper()
        if not email:
            return render_template("apology.html", msg="Please enter email")
        # Make sure submitted
        elif not password:
            return render_template("apology.html", msg="Please enter password")
        # Make sure there are no accounts with the same email
        rows = db.execute("SELECT * FROM users WHERE email = ?", email)
        # Make sure email does not exist
        if len(rows) == 1:
            return render_template("apology.html", msg = "An account is using this email")
        # Check that both passwords are the same
        if password != confirmation:
            return render_template("apology.html", msg ="Passwords do not match")

        # Enter data into database
        new_user = db.execute("INSERT INTO users (email, password, currency) VALUES (?, ?, ?)", email, generate_password_hash(password), currency)
        db.execute("INSERT INTO balances (current, saving, currency) VALUES (?, ?, ?)", 0, 0, currency)
        # Log user in
        session["user_id"] = new_user

        return redirect("/")
    else:
        # Go to main page
        return render_template("register.html", currencies=sorted(currencies))
    
@app.route("/balance", methods=["GET", "POST"])
@login_required
def balance():
    # 
    user_id = session["user_id"]
    transactions_list = transacition_list_finder(user_id)[:5]
    balance = db.execute("SELECT * FROM balances WHERE id = ?", user_id)
    return render_template("balance.html", balances=balance, transactions=transactions_list, currency=balance[0]["currency"])

@app.route("/stats")
@login_required
def stats():
    # 
    user_id = session["user_id"]
    # Create list of transaction values to use in the line graph
    transactions_list = reversed(transacition_list_finder(user_id)[:5])
    transactions_list_values = []
    for transaction in transactions_list:
        transactions_list_values.append(transaction["value"])
    # Pie chart data
    reasons = []
    reasons_counted = set()
    reason_count = {}
    for transaction in transacition_list_finder(user_id):
        reasons.append(transaction["reason"])
    for reason in reasons:
        reasons_counted.add(reason)
        reason_count[reason] = 0
        for _ in reasons:
            if reason == _:
                reason_count[reason] += 1
    count = []
    for reason in reasons_counted:
        count.append(reason_count[reason])
    # Calculate net value of last 5 transactions
    net_value = 0
    spent = 0
    added = 0
    expenses = []
    transaction_values = []
    for transaction in transacition_list_finder(user_id):
        transaction_values.append(float(transaction["value"]))
    for value in transaction_values:
        if float(value) > 0:
            added += float(value)
        else:
            spent += float(value)
        ###
        net_value += float(value)
    ###
    expenses.append(net_value)
    expenses.append(added)
    expenses.append(spent)
    ###
    return render_template("stats.html", reason_count=count,expenses=expenses, reasons=list(reasons_counted), values=transactions_list_values)

@app.route("/recommendations")
@login_required
def recommendations():
    user_id = session["user_id"]
    currency = db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]["currency"]
    # Return recomendations for monthly habits based on transactions
    net_value = 0
    expenses = []
    for transaction in transacition_list_finder(user_id):
        ###
        net_value += float(transaction["value"])
    ###
    expenses.append(net_value)
    # Check if enough data is present
    if len(transacition_list_finder(user_id)) < 10:
        return render_template("recommendations_error.html", msg="Not enough data to access this feature. Minimum 10 transactions.")
    # Reasons:
    reasons = []
    reason_count = {}
    reasons_counted = set()
    for transaction in transacition_list_finder(user_id):
        if float(transaction["value"]) < 0:
            reasons.append(transaction["reason"])
    for reason in reasons:
        reasons_counted.add(reason)
        reason_count[reason] = 0
        for _ in reasons:
            if reason == _:
                reason_count[reason] += 1
    ###
    large_expenses = {}
    mid_expenses = {}
    for reason in list(reasons_counted):
        percent = 100 * (reason_count[reason] / len(transacition_list_finder(user_id)))
        if percent >= 30:
            large_expenses[reason] = 0
        elif percent >= 20:
            mid_expenses[reason] = 0
    # make predictions
    transacition_list = transacition_list_finder(user_id)
    ###
    large_recomendations = []
    mid_recomendations = []
    ###
    if large_expenses:
        for key in large_expenses.keys():
            for transaction in transacition_list:
                if transaction["reason"] == key:
                    large_expenses[reason] += float(transaction["value"]) * -1
        ###
        for key in large_expenses.keys():
            large_recomendations.append(f"You spent {currency}:{large_expenses[key]} on {key}, that's over 30% of your expenses! Consider cutting back to save.")
        
    if mid_expenses:
        for key in mid_expenses.keys():
            for transaction in transacition_list:
                if transaction["reason"] == key:
                    mid_expenses[reason] += float(transaction["value"]) * -1
        ###
        for key in mid_expenses.keys():
            mid_recomendations.append(f"You spent {currency}:{mid_expenses[key]} on {key}, that's over 20% of your expenses! Consider cutting back to save.")
       
    ###
    if net_value <= 50:
        large_recomendations.append("Low balance! Do something to get rich 🤑!")   
    ###
    if len(large_recomendations) < 1 and len(mid_recomendations) < 1:
        return render_template("recommendations_error.html", msg="Doing great! No current recomendations.")
    if len(large_recomendations) > 0 and len(mid_recomendations) > 0:
        return render_template("recommendations.html", large_r=large_recomendations, mid_r=mid_recomendations)
    if len(large_recomendations) > 0:
        return render_template("recommendations.html", large_r=large_recomendations)
    if len(mid_recomendations) > 0:
        return render_template("recommendations.html", mid_r=mid_recomendations)

#####################
# Balance Functions #
@app.route("/add_money", methods=["GET", "POST"])
def add_money():
    user_id = session["user_id"]

    if request.method == "POST":
        # get ammount to transfer
        value = request.form.get("value")
        balance = request.form.get("balance")
        reason = request.form.get("reason").title().strip()
        # check input
        if not value:
            return render_template("apology.html", msg="Please enter amount")
        # Make sure submitted
        elif not balance:
            return render_template("apology.html", msg="Please choose a balance") 
        elif not reason:
            return render_template("apology.html", msg="Please list a reason") 
        # get newest balance values
        cur_balance = db.execute("SELECT * FROM balances WHERE id = ?", user_id)
        total_balance = db.execute("SELECT * FROM users WHERE id = ?", user_id)
        # add to transactions
        cur_equ = round(c.convert(int(value), cur_balance[0]["currency"], cur_balance[0]["currency"]), 2)
        if os.path.isfile(f"transactions/ID {user_id}.csv"):
            with open(f"transactions/ID {user_id}.csv", "a") as transactions_add:
                transaction = {"id": user_id, "value": value, "reason": reason, "cur_equ": cur_equ}
                writer = csv.DictWriter(transactions_add, fieldnames=["id", "value", "reason", "cur_equ"])
                writer.writerow(transaction)
        else:
            with open(f"transactions/ID {user_id}.csv", "w") as transactions_add:
                transaction = {"id": user_id, "value": value, "reason": reason, "cur_equ": cur_equ}
                writer = csv.DictWriter(transactions_add, fieldnames=["id", "value", "reason", "cur_equ"])
                writer.writeheader()
                writer.writerow(transaction)

        # Update and reload page
        db.execute("UPDATE balances SET (?) = ? WHERE id = ?", balance, float(cur_balance[0][balance] + float(value)), user_id)
        db.execute("UPDATE users SET balance = ? WHERE id = ?", float(total_balance[0]["balance"] + float(value)), user_id)
        ###
        return redirect("/balance")
    else:
        return redirect("/balance")
    
@app.route("/remove_money", methods=["GET", "POST"])
def remove_money():
    user_id = session["user_id"]
    if request.method == "POST":
        # get ammount to transfer
        value = request.form.get("value")
        balance = request.form.get("balance")
        reason = request.form.get("reason").title().strip()
        # check input
        if not value:
            return render_template("apology.html", msg="Please enter amount")
        # Make sure submitted
        elif not balance:
            return render_template("apology.html", msg="Please choose a balance") 
        elif not reason:
            return render_template("apology.html", msg="Please list a reason") 
        # get newest balance values
        cur_balance = db.execute("SELECT * FROM balances WHERE id = ?", user_id)
        total_balance = db.execute("SELECT * FROM users WHERE id = ?", user_id)
        # check for sufficent funds
        if float(value) > float(cur_balance[0][balance]):
            return render_template("apology.html", msg="Insufficient funds")
        # add to transactions
        cur_equ = round(c.convert(int(value), cur_balance[0]["currency"], cur_balance[0]["currency"]), 2)
        if os.path.isfile(f"transactions/ID {user_id}.csv"):
            with open(f"transactions/ID {user_id}.csv", "a") as transactions_add:
                transaction = {"id": user_id, "value": float(f"-{value}"), "reason": reason, "cur_equ": float(f"-{cur_equ}")}
                writer = csv.DictWriter(transactions_add, fieldnames=["id", "value", "reason", "cur_equ"])
                writer.writerow(transaction)
        else:
            with open(f"transactions/ID {user_id}.csv", "w") as transactions_add:
                transaction = {"id": user_id, "value": float(f"-{value}"), "reason": reason, "cur_equ": float(f"-{cur_equ}")}
                writer = csv.DictWriter(transactions_add, fieldnames=["id", "value", "reason", "cur_equ"])
                writer.writeheader()
                writer.writerow(transaction)
        # Update and reload page
        db.execute("UPDATE balances SET (?) = ? WHERE id = ?", balance, float(cur_balance[0][balance] - float(value)), user_id)
        db.execute("UPDATE users SET balance = ? WHERE id = ?", float(total_balance[0]["balance"] - float(value)), user_id)
        ###
        return redirect("/balance")
    else:
        return redirect("/balance")


@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    user_id = session["user_id"]
    if request.method == "POST":
        # get ammount to transfer
        value = request.form.get("value")
        from_balance = request.form.get("from_balance")
        to_balance = request.form.get("to_balance")
        to_id = request.form.get("to_id")
        reason = request.form.get("reason").title().strip()
        # check input
        if not value:
            return render_template("apology.html", msg="Please enter amount")
        # Make sure submitted
        elif not to_id:
            return render_template("apology.html", msg="Please specify the recipient ID")
        elif not from_balance:
            return render_template("apology.html", msg="Please choose a balance")
        elif not to_balance:
            return render_template("apology.html", msg="Please choose the recipient balance")  
        elif not reason:
            return render_template("apology.html", msg="Please list a reason")
        # get currencies
        from_cur = db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]["currency"]
        to_cur = db.execute("SELECT * FROM users WHERE id = ?", to_id)[0]["currency"]
        # get newest balance values for sender
        from_cur_balance = db.execute("SELECT * FROM balances WHERE id = ?", user_id)
        from_total_balance = db.execute("SELECT * FROM users WHERE id = ?", user_id)
        # get newest balance values for recipient
        to_cur_balance = db.execute("SELECT * FROM balances WHERE id = ?", user_id)
        try:
            to_total_balance = db.execute("SELECT * FROM users WHERE id = ?", int(to_id))
            print(to_total_balance[0])
        except:
            return render_template("apology.html", msg="Invalid recipient")
        # remove amount from sender
        if float(value) > float(from_cur_balance[0][from_balance]):
            return render_template("apology.html", msg="Insufficient funds")
        # add to transactions
        cur_equ_from = round(c.convert(int(value), from_cur, to_cur), 2)
        print(to_cur_balance[0]["currency"])
        if os.path.isfile(f"transactions/ID {user_id}.csv"):
            with open(f"transactions/ID {user_id}.csv", "a") as transactions_add:
                transaction = {"id": user_id, "value": float(f"-{value}"), "reason": reason, "cur_equ": float(f"-{cur_equ_from}")}
                writer = csv.DictWriter(transactions_add, fieldnames=["id", "value", "reason", "cur_equ"])
                writer.writerow(transaction)
        else:
            with open(f"transactions/ID {user_id}.csv", "w") as transactions_add:
                transaction = {"id": user_id, "value": float(f"-{value}"), "reason": reason, "cur_equ": float(f"-{cur_equ_from}")}
                writer = csv.DictWriter(transactions_add, fieldnames=["id", "value", "reason", "cur_equ"])
                writer.writeheader()
                writer.writerow(transaction)
        # Update sender info
        db.execute("UPDATE balances SET (?) = ? WHERE id = ?", from_balance, round(float(from_cur_balance[0][from_balance] - float(value)),2 ), user_id)
        db.execute("UPDATE users SET balance = ? WHERE id = ?", round(float(from_total_balance[0]["balance"] - float(value)), 2), user_id)
        ######
        # Add money to recipeint 
        ######
        if os.path.isfile(f"transactions/ID {to_id}.csv"):
            with open(f"transactions/ID {to_id}.csv", "a") as transactions_add:
                transaction = {"id": user_id, "value": cur_equ_from, "reason": reason, "cur_equ": float(value)}
                writer = csv.DictWriter(transactions_add, fieldnames=["id", "value", "reason", "cur_equ"])
                writer.writerow(transaction)
        else:
            with open(f"transactions/ID {to_id}.csv", "w") as transactions_add:
                transaction = {"id": user_id, "value": cur_equ_from, "reason": reason, "cur_equ": float(value)}
                writer = csv.DictWriter(transactions_add, fieldnames=["id", "value", "reason", "cur_equ"])
                writer.writeheader()
                writer.writerow(transaction)

        # Update recipent info
        db.execute("UPDATE balances SET (?) = ? WHERE id = ?", to_balance, round(float(to_cur_balance[0][to_balance] + cur_equ_from), 2), to_id)
        db.execute("UPDATE users SET balance = ? WHERE id = ?", round(float(to_total_balance[0]["balance"] + cur_equ_from), 2), to_id)
        ###
        return redirect("/balance")
    else:
        return redirect("/balance")
         
##################
# Reset Function #

@app.route("/reset")
def reset():
    user_id = session["user_id"]
    if os.path.isfile(f"transactions/ID {user_id}.csv"):
        with open(f"transactions/ID {user_id}.csv", "w") as transactions_file:
            writer = csv.DictWriter(transactions_file, fieldnames=["id", "value", "reason", "cur_equ"])
            writer.writeheader()

    db.execute("UPDATE balances SET (current, saving) = (0,0) WHERE id = ?", user_id)
    db.execute("UPDATE users SET balance = 0 WHERE id = ?", user_id)

    return redirect("/")


@app.route("/help")
def help():
    return render_template("help.html")
    
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")
