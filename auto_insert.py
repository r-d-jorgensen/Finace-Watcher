"""Scrapes All Bank transactions from PDF File and inserts into DB"""
import sys
import csv
import argparse
from enum import Enum
from datetime import datetime
from dotenv import load_dotenv
from db_helper import sql_get, sql_insert

CHANGE_TYPES = ["debit", "credit"]

class SupportedInstitute(Enum):
    """Supported Institute with Parsing"""
    NAVY_FEDERAL = "Navy Federal"
    CHARLES_SCHWAB = "Charles Schwab"

class Record:
    """Record Structure matching DB"""
    def __init__(self, record_id:int=0, account_id:int=0, category_id:int=0, amount:float=0,
                 business:str=0, note:str=0, transaction_date:datetime=None):
        self.record_id = record_id
        self.account_id = account_id
        self.category_id = category_id
        self.amount = amount
        self.business = business
        self.note = note
        self.transaction_date = transaction_date

    def record_exists(self)->bool:
        """Get the record into the db"""
        sql_statement = "SELECT * FROM records WHERE account_id = ? AND category_id = ? AND \
            amount = ? AND business = ? AND note = ? AND transaction_date = ?;"
        sql_params = [self.account_id, self.category_id, self.amount, self.business,
                      self.note, self.transaction_date]
        results = sql_get(sql_statement, sql_params)
        return results != []

    def insert_record(self)->None:
        """Insert the record into the db"""
        if self.record_exists():
            return
        sql_statement = "INSERT INTO records \
            (account_id, category_id, amount, business, note, transaction_date) \
            VALUES (?, ?, ?, ?, ?, ?);"
        sql_params = [self.account_id, self.category_id, self.amount, self.business,
                      self.note, self.transaction_date]
        self.account_id = sql_insert(sql_statement, sql_params)

    def get_category(self)->None:
        """Gets the category of the transaction"""
        try:
            sql_statement = "SELECT category_id FROM records \
                WHERE account_id = ? AND business LIKE ?;"
            return sql_get(sql_statement, [self.account_id, self.business])[0][0]
        except IndexError:
            sql_statement = "SELECT * FROM categories WHERE account_id = ?;"
            categories = sql_get(sql_statement, [self.account_id])
            choice = 1
            while True:
                print("---------------------------------------------------------------")
                index = 0
                for category in categories:
                    index += 1
                    print(f"{index}: {category[2]}")
                print("0: None of the Above")
                try:
                    print(f"${self.amount} from '{self.business}' with note "+
                          f"'{self.note.strip()}' on self.transaction_date.date()")
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
                    self.category_id = sql_insert(
                        sql_statement,
                        [self.account_id, category_name, change_type])
                if 0 < choice <= len(categories):
                    self.category_id = categories[choice-1][0]

def parse_navy_federal_csv(csv_file:str, account_id:int)->list[Record]:
    """Parses all transaction info from credit card csv"""
    transactions = []
    with open(csv_file, encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=',')
        next(reader)
        for row in reader:
            if ("transfer to credit card" in row[10].lower() or
                "credit card payment" in row[10].lower()):
                continue
            record = Record(
                account_id=account_id,
                amount=float(row[2]),
                business=row[10],
                note=row[11],
                transaction_date=datetime.strptime(row[1], "%m/%d/%Y"))
            transactions.append(record)
    return transactions

def parse_charles_schwab_investment_csv(csv_file:str, account_id:int)->list[Record]:
    """Parses all transaction info from charles swab csv"""
    transactions = []
    with open(csv_file, encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=',')
        next(reader)
        for row in reader:
            if not row[7]:
                continue
            record = Record(
                account_id=account_id,
                amount=abs(float(row[7].replace("$", ""))),
                business=row[1],
                note=f"{row[3]} {row[2]}",
                transaction_date=datetime.strptime(row[0][:10], "%m/%d/%Y"))
            transactions.append(record)
    return transactions

def parse_charles_schwab_checking_csv(csv_file:str, account_id:int)->list[Record]:
    """Parses all transaction info from charles swab csv"""
    transactions = []
    with open(csv_file, encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=',')
        next(reader)
        for row in reader:
            if "Posted" not in row[1]:
                continue
            amount = (row[6][1:] if row[6] != "" else row[5][1:]).replace(",", "")
            record = Record(
                account_id=account_id,
                amount=amount,
                business=row[4],
                note=row[2],
                transaction_date=datetime.strptime(row[0], "%m/%d/%Y"))
            transactions.append(record)
    return transactions

def transaction_inserter(account_id:int, file:str, institute:str)->None:
    """Driver function of script"""
    transactions = []
    if SupportedInstitute[institute] == SupportedInstitute.NAVY_FEDERAL and ".csv" in file:
        transactions = parse_navy_federal_csv(file, account_id)
    elif SupportedInstitute[institute] == SupportedInstitute.CHARLES_SCHWAB:
        if "Checking" in file:
            transactions = parse_charles_schwab_checking_csv(file, account_id)
        elif "Individual" in file or "Roth" in file:
            transactions = parse_charles_schwab_investment_csv(file, account_id)
    else:
        print("Not a valid File")
        sys.exit()

    insertions = 0
    for record in transactions:
        record:Record
        record.get_category()
        if record.record_exists():
            record.insert_record()
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
        for _, _, name, _ in accounts:
            index += 1
            print(f"{index}: {name}")
        choice = input("Which account - ")
        if 0 < int(choice) and int(choice) <= index:
            break
    return accounts[int(choice)-1][0]

def main()->None:
    """Main Driver"""
    parser = argparse.ArgumentParser(description="Insert PDF and CSV data")
    parser.add_argument("-f", "--file", help='Transaction File Name', required=True)
    parser.add_argument("-i", "--institute", help='Institute of the transactions', required=True)
    args = parser.parse_args()
    load_dotenv()
    account_id = get_account_id()
    transaction_inserter(account_id, args.file, args.institute)

if __name__ == "__main__":
    main()
