from flask import redirect, session
from functools import wraps
import os
import csv


def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def transacition_list_finder(user_id):
    if os.path.isfile(f"transactions/ID {user_id}.csv"):
        with open(f"transactions/ID {user_id}.csv", "r") as transactions:
            reader = csv.DictReader(transactions, fieldnames=["id", "value", "reason", "cur_equ"])
            transactions_list = []
            i = 0
            for row in reader:
                if i == 0:
                    i += 1
                else:
                    transactions_list.append(row)
            transactions_list_final = []
            for transaction in reversed(transactions_list):
                transactions_list_final.append(transaction)
            return transactions_list_final
    else:
        transactions_list = []
        return transactions_list

