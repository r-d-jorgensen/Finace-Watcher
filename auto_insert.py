"""Scrapes All Bank transactions from PDF File and inserts into DB"""
import sys
import csv
import sqlite3
import argparse
from enum import Enum
from datetime import datetime
from dotenv import load_dotenv
sqlite3.register_adapter(datetime, lambda dt: dt.strftime("%Y-%m-%d"))

CHANGE_TYPES = ["debit", "credit"]

class SupportedInstitute(Enum):
    """Supported Institute with Parsing"""
    NAVY_FEDERAL = "Navy Federal"
    CHARLES_SCHWAB = "Charles Schwab"

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

def get_category(account_id:int, amount:float, business:str, note:str,
                 transaction_date:datetime)->int:
    """Gets the category of the transaction"""
    try:
        sql_statement = "SELECT category_id FROM records WHERE account_id = ? AND business LIKE ?;"
        return sql_get(sql_statement, [account_id, business])[0][0]
    except IndexError:
        sql_statement = "SELECT * FROM categories WHERE account_id = ?;"
        categories = sql_get(sql_statement, [account_id])
        choice = 1
        while True:
            print("---------------------------------------------------------------")
            index = 0
            for category in categories:
                index += 1
                print(f"{index}: {category[2]}")
            print("0: None of the Above")
            try:
                print(f"${amount} from '{business}' with note '{note.strip()}' on " +
                      transaction_date.date())
                choice = int(input("Select the category that best describes the above record - "))
            except ValueError:
                print("The value imputed is not a integer")
            if choice == 0:
                category_name = input("What is the name of the new category? - ")
                while True:
                    change_type = input("What is the change type? - ")
                    if change_type.lower() in CHANGE_TYPES:
                        break
                sql_statement = "INSERT INTO categories (account_id, category, change_type) \
                    VALUES (?, ?, ?);"
                return sql_insert(sql_statement, [account_id, category_name, change_type])
            if 0 < choice <= len(categories):
                return categories[choice-1][0]

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

def transaction_inserter(account_id:int, file:str, institute:str)->None:
    """Driver function of script"""
    sql_check_statement = "SELECT * FROM records WHERE account_id = ? AND category_id = ? AND \
        amount = ? AND business = ? AND note = ? AND transaction_date = ?;"
    sql_insert_statement = "INSERT INTO records \
            (account_id, category_id, amount, business, note, transaction_date) \
            VALUES (?, ?, ?, ?, ?, ?);"

    transactions = []
    if SupportedInstitute[institute] == SupportedInstitute.NAVY_FEDERAL and ".csv" in file:
        transactions = parse_navy_federal_csv(file)
    elif SupportedInstitute[institute] == SupportedInstitute.CHARLES_SCHWAB:
        if "Checking" in file:
            transactions = parse_charles_schwab_checking_csv(file)
        elif "Individual" in file or "Roth" in file:
            transactions = parse_charles_schwab_investment_csv(file)
    else:
        print("Not a valid File")
        sys.exit()

    insertions = 0
    for record in transactions:
        record[0] = account_id
        record[1] = get_category(account_id, record[2], record[3], record[4], record[5])
        if len(sql_get(sql_check_statement, record)) == 0:
            sql_insert(sql_insert_statement, record)
            insertions += 1
    if insertions == 0:
        print("No new transactions")
    else:
        print(f"{insertions} records where added the DB")

def get_account_id()->int:
    """Get account id from account name"""
    sql_statement = "SELECT * FROM accounts;"
    accounts = sql_get(sql_statement, [])
    choice = 0
    while True:
        index = 0
        for _, _, name in accounts:
            index += 1
            print(f"{index}: {name}")
        choice = input("Which account - ")
        if 0 < int(choice) and int(choice) <= index:
            break
    return accounts[int(choice)-1][0]

def main()->None:
    """Main Driver"""
    parser = argparse.ArgumentParser(description="Insert PDF and CSV data")
    # parser.add_argument("-b", "--book", help='Book ID', default=1, required=False)
    parser.add_argument("-f", "--file", help='Transaction File Name', required=True)
    parser.add_argument("-i", "--institute", help='Institute of the transactions', required=True)
    args = parser.parse_args()
    load_dotenv()
    account_id = get_account_id()
    transaction_inserter(account_id, args.file, args.institute)

if __name__ == "__main__":
    main()
