"""Scrapes All Bank transactions from PDF File and inserts into DB"""
import os
import re
import sys
import csv
import sqlite3
import argparse
from enum import Enum
from datetime import datetime
from dotenv import load_dotenv
from pypdf import PdfReader
sqlite3.register_adapter(datetime, lambda dt: dt.strftime("%Y-%m-%d"))

CHANGE_TYPES = ["debit", "credit"]

class SupportedInstitute(Enum):
    """Supported Institute with Parsing"""
    NAVY_FEDERAL = "Navy Federal"
    CHARLES_SCHWAB = "Charles Schwab"

class NoData(Exception):
    """Error is raised when no data is retrieved from system"""
    def __init__(self, message="Data Not pulled correctly"):
        super().__init__(message)

def parse_navy_federal_credit_pdf(pdf_file:str)->list:
    """Parses all transaction info from credit card pdf"""
    transactions = []
    transaction_debits = []
    reader = PdfReader(pdf_file)
    debits_found, credits_found = False, False

    start_of_debits = "Trans Date Post Date Reference No. Description Submitted By Amount"
    end_of_debits = "TOTAL PAYMENTS AND CREDITS"
    mobile_payment = "MOB PAYMENT RECEIVED"
    online_payment = "NFO PAYMENT RECEIVED"

    start_of_credits = "Trans Date Post Date Reference No."
    end_of_credits = f"TOTAL New Activity for {os.getenv("LEGAL_NAME")}"
    def parse_transaction_line(data_line:str)->list:
        """Takes pdf str and returns transaction record"""
        holder = ""
        consumed = 0
        data_point = [0, 0, 0.0, "", "", "", datetime]
        for char in data_line:
            if (char == " " and consumed < 3) or char == "$":
                if consumed == 0:
                    data_point[5] = datetime.strptime(holder[:6] + "20" + holder[6:], "%m/%d/%Y")
                elif consumed == 3:
                    data_point[3] = holder[:25].strip()
                    data_point[4] = holder[25:]
                holder = ""
                consumed += 1
            else:
                holder += char
        data_point[2] = float(holder.replace(",", ""))
        return data_point

    for page in reader.pages[1:]:
        text = page.extract_text().split("\n")
        for line in text:
            if end_of_debits in line:
                debits_found = False
            elif end_of_credits in line:
                if transaction_debits:
                    for record in transaction_debits:
                        print(record)
                    print("------------------------------------------")
                    print("INSERT INTO records (bank_account_id, category_id, \
                          amount, business, location, note, transaction_date)")
                    print("VALUES (1, 0, 0.00, '', ', '', '');")
                    print("------------------------------------------")
                return transactions

            if start_of_debits in line:
                debits_found = True
            elif start_of_credits in line:
                credits_found = True
            elif debits_found:
                if mobile_payment in line or online_payment in line:
                    continue
                transaction_debits.append(line)
            elif credits_found:
                if "TRANSACTIONS" in line:
                    continue
                if "Page " in line:
                    continue
                if os.getenv("LEGAL_NAME") in line:
                    continue

                data_point = parse_transaction_line(line)
                transactions.append(data_point)
    raise NoData()

def parse_navy_federal_csv(csv_file:str)->list:
    """Parses all transaction info from credit card csv"""
    transactions = []
    with open(csv_file, encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=',')
        next(reader)
        for row in reader:
            if ("transfer to credit card" in row[10].lower() or
                "credit card payment" in row[10].lower()):
                continue
            data_point = [0, 0,
                        float(row[2]),
                        row[10],
                        row[11],
                        datetime.strptime(row[1], "%m/%d/%Y")]
            transactions.append(data_point)
    return transactions

def parse_navy_federal_account_pdf(pdf_file:str)->list:
    """Parses all transaction info from account pdf"""
    transaction_info, transaction_amount = [], []
    reader = PdfReader(pdf_file)
    start_of_transactions = "Beginning Balance"
    end_of_transaction_info = f"For {os.getenv("LEGAL_NAME")}"
    start_of_transaction_amount = "Joint Owner"
    end_of_transactions = " -Statement Period"
    transaction_info_found = False
    record_info = True
    transaction_amount_found = False
    def parse_transaction_line(data_line:str)->list:
        """Takes pdf str and returns transaction record"""
        data_point = [0, 0, 0.0, "", "NA", "",
            datetime.strptime(data_line[:5] + "-" + str(datetime.now().year), "%m-%d-%Y")
        ]
        if "Reward Redemption" in data_line:
            data_point[2] = float(data_line[24:].split()[0].replace(",", ""))
            data_point[3] = "Reward Redemption"
            return data_point
        if "Dividend" in data_line:
            data_point[2] = float(data_line[15:].split()[0].replace(",", ""))
            data_point[3] = "Dividend"
            return data_point

        holder = ""
        for char in data_line[16:]:
            if char == "~":
                data_point[3] = holder
                holder = ""
            else:
                holder += char
        data_point[2] = float(holder.split()[0].replace(",", ""))
        if "Paid To" in data_line:
            data_point[2] *= -1
        return data_point

    for page in reader.pages:
        text = page.extract_text().split("\n")
        for line in text:
            if start_of_transactions in line:
                transaction_info_found = True
                continue
            if not transaction_info_found:
                continue

            if end_of_transactions in line:
                transactions = []
                for info, amount in zip(transaction_info, transaction_amount):
                    raw_string = re.sub(r"\s+", " ", info + "~" + amount)
                    if "Transfer To Credit Card" in raw_string:
                        continue
                    transactions.append(parse_transaction_line(raw_string))
                return transactions

            if end_of_transaction_info in line:
                record_info = False
                continue
            if record_info:
                transaction_info.append(line)

            if start_of_transaction_amount in line:
                transaction_amount_found = True
                continue
            if not transaction_amount_found:
                continue
            transaction_amount.append(line)
    raise NoData()

def parse_charles_schwab_investment_csv(csv_file:str)->list:
    """Parses all transaction info from charles swab csv"""
    transactions = []
    with open(csv_file, encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=',')
        next(reader)
        for row in reader:
            if not row[7]:
                continue
            data_point = [0, 0,
                abs(float(row[7].replace("$", ""))),
                row[1],
                f"{row[3]} {row[2]}",
                datetime.strptime(row[0][:10], "%m/%d/%Y")]
            transactions.append(data_point)
    return transactions

def parse_charles_schwab_checking_csv(csv_file:str)->list:
    """Parses all transaction info from charles swab csv"""
    transactions = []
    with open(csv_file, encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=',')
        next(reader)
        for row in reader:
            if "Posted" not in row[1]:
                continue
            data_point = [0, 0,
                float(row[6][1:].replace(",", "")) if row[6] != ""
                    else float(row[5][1:].replace(",", "")),
                row[4],
                row[2],
                datetime.strptime(row[0], "%m/%d/%Y")]
            transactions.append(data_point)
    return transactions

def get_category(account_id:int, amount:float, business:str, note:str, transaction_date:datetime)->int:
    """Gets the category of the transaction"""
    try:
        sql_statement = "SELECT category_id FROM records WHERE account_id = ? AND business LIKE ?;"
        category_id = sql_get(sql_statement, [account_id, business])[0][0]
    except IndexError:
        sql_statement = "SELECT * FROM categories WHERE account_id = ?;"
        categories = sql_get(sql_statement, [account_id])
        category_id = None
        while category_id is None:
            print("---------------------------------------------------------------")
            for category in categories:
                print(f"{category[0]}: {category[2]}")
            print("0: None of the Above")
            try:
                print(f"${amount} from '{business}' with note '{note.strip()}' on {transaction_date.date()}")
                category_id = int(input("Select the category that best describes the above record - "))
            except ValueError:
                print("The value imputed is not a integer")
        if category_id == 0:
            category_name = input("What is the name of the new category? - ")
            while True:
                change_type = input("What is the change type? - ")
                if change_type.lower() in CHANGE_TYPES:
                    break
            sql_statement = "INSERT INTO categories (account_id, category, change_type) \
                VALUES (?, ?, ?);"
            category_id = sql_insert(sql_statement, [account_id, category_name, change_type])
    return category_id

def sql_get(sql_statement:str, sql_parameters:list)->list:
    """Gets data from sql db"""
    rows = []
    try:
        db_connection = sqlite3.connect("finance.db")
        cursor = db_connection.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')
        cursor.execute(sql_statement, sql_parameters)
        rows = cursor.fetchall()
        db_connection.commit()
        db_connection.close()
    except sqlite3.Error as error:
        print("Data was not retrieved from DB")
        print(error)
        print(sql_statement)
        print(sql_parameters)
        sys.exit()
    return rows

def sql_insert(sql_statement:str, sql_parameters:list)->int:
    """Inserts single row into sql db and returns id"""
    insert_id = 0
    try:
        db_connection = sqlite3.connect("finance.db")
        cursor = db_connection.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')
        cursor.execute(sql_statement, sql_parameters)
        insert_id = cursor.lastrowid
        db_connection.commit()
        db_connection.close()
    except sqlite3.Error as error:
        print("Data was not inserted into DB")
        print(error)
        print(sql_statement)
        print(sql_parameters)
    return insert_id

def transaction_inserter(bank_account_id:int, file:str, institute:str)->None:
    """Driver function of script"""
    sql_check_statement = "SELECT * FROM records WHERE account_id = ? AND category_id = ? AND \
        amount = ? AND business = ? AND note = ? AND transaction_date = ?;"
    sql_insert_statement = "INSERT INTO records \
            (account_id, category_id, amount, business, note, transaction_date) \
            VALUES (?, ?, ?, ?, ?, ?);"

    transactions = []
    if SupportedInstitute[institute] == SupportedInstitute.NAVY_FEDERAL:
        if ".pdf" in file:
            if "VISA" in file:
                transactions = parse_navy_federal_credit_pdf(file)
            elif "STMSS" in file:
                transactions = parse_navy_federal_account_pdf(file)
        if ".csv" in file:
            transactions = parse_navy_federal_csv(file)
        else:
            print("Not a valid File")
            sys.exit()
    elif SupportedInstitute[institute] == SupportedInstitute.CHARLES_SCHWAB:
        if ".csv" in file:
            if "Checking" in file:
                transactions = parse_charles_schwab_checking_csv(file)
            elif "Individual" in file or "Roth" in file:
                transactions = parse_charles_schwab_investment_csv(file)
            else:
                print("Not a valid File")
                sys.exit()

    insertions = 0
    for record in transactions:
        record[0] = bank_account_id
        print(record)
        continue
        record[1] = get_category(bank_account_id, record[2], record[3], record[4], record[5])
        if len(sql_get(sql_check_statement, record)) == 0:
            sql_insert(sql_insert_statement, record)
            insertions += 1
    if insertions == 0:
        print("No new transactions")
    else:
        print(f"{insertions} records where added the DB")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Insert PDF and CSV data")
    # parser.add_argument("-b", "--book", help='Book ID', default=1, required=False)
    parser.add_argument("-a", "--account", help='Account ID', required=True)
    parser.add_argument("-f", "--file", help='Transaction File Name', required=True)
    parser.add_argument("-i", "--institute", help='Institute of the transactions', required=True)
    args = parser.parse_args()
    load_dotenv()
    transaction_inserter(args.account, args.file, args.institute)
