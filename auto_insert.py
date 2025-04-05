"""Scrapes All Bank transactions from PDF File and inserts into DB"""
import sys
import csv
import argparse
from enum import Enum
from datetime import datetime
from dotenv import load_dotenv
from db_helper import sql_get, sql_insert, sql_update

class RecordChangeType(Enum):
    """Types of changes that records embody"""
    CREDIT_ACCOUNT = "Credit Account"
    DEBIT_ACCOUNT = "Debit Account"
    BUY_ASSET = "Buy Asset"
    SELL_ASSET = "Sell Asset"
    MARKET_UPDATE = "Market Update"

RECORD_CHANGE_TYPES = [change_type for change_type in RecordChangeType]

class SupportedInstitute(Enum):
    """Supported Institute with Parsing"""
    NAVY_FEDERAL = "Navy Federal"
    CHARLES_SCHWAB = "Charles Schwab"

class Account:
    """Account Structure matching DB"""
    def __init__(self, account_id:int=0):
        sql_statement = "SELECT * FROM accounts WHERE account_id = ?;"
        sql_params = [account_id]
        results = sql_get(sql_statement, sql_params)
        if results == []:
            print("No account found")
            sys.exit()
        self.account_id = account_id
        self.book_id = results[0][1]
        self.account = results[0][2]
        self.purpose = results[0][3]
        self.cash_funds = results[0][4]
        self.investment_worth = results[0][5]
        self.debt_total = results[0][6]

    def update_cash_funds(self, amount:float, change_type:RecordChangeType)->None:
        """Update total fund counter"""
        if change_type == RecordChangeType.DEBIT_ACCOUNT:
            self.cash_funds += amount
        elif change_type == RecordChangeType.CREDIT_ACCOUNT:
            self.cash_funds -= amount
        else:
            print("Not a supported record change type", amount, change_type.name)
            return

        sql_statement = "UPDATE accounts \
            SET cash_funds = ? \
            WHERE account_id = ?"
        sql_params = [self.cash_funds, self.account_id]
        sql_update(sql_statement, sql_params)

    def update_investment_worth(self, amount:float, change_type:RecordChangeType)->None:
        """Update total investment counter"""
        if change_type == RecordChangeType.BUY_ASSET:
            self.investment_worth += amount
        elif change_type == RecordChangeType.SELL_ASSET:
            self.investment_worth -= amount
        elif change_type == RecordChangeType.MARKET_UPDATE:
            pass
        else:
            print("Not a supported record change type", amount, change_type.name)
            return

        sql_statement = "UPDATE account \
            SET investment_worth = ? \
            WHERE account_id = ?"
        sql_params = [self.investment_worth, self.account_id]
        sql_update(sql_statement, sql_params)

    def update_debt_total(self, amount:float, change_type:RecordChangeType)->None:
        """Update total debt counter"""
        print("Not a supported record change type", amount, change_type.name)

class Asset():
    """Asset Structure matching DB"""
    def __init__(self, asset_id:int=0, account:Account=None, name:str=None, quantity:float=0,
                 market_value:float=0, note:str=None):
        self.asset_id = asset_id
        self.account = account
        self.name = name
        self.quantity = quantity
        self.market_value = market_value
        self.note = note
        if asset_id == 0:
            self.get_asset_id()

    def get_asset_id(self)->None:
        """Get asset from DB"""
        sql_statement = "SELECT * FROM assets WHERE account_id = ? AND name = ?;"
        sql_params = [self.account.account_id, self.name]
        results = sql_get(sql_statement, sql_params)
        if results == []:
            return
        self.asset_id = results[0][0]

    def update_asset(self, change_type:RecordChangeType=None)->None:
        """Update asset in DB"""
        if self.asset_id == 0:
            sql_statement = "INSERT INTO assets \
                (account_id, name, quantity, market_value, note) \
                VALUES (?, ?, ?, ?, ?, ?);"
            sql_params = [self.account.account_id, self.name, self.quantity, self.note]
            self.asset_id = sql_insert(sql_statement, sql_params)
            print("--------Asset added to DB")
        else:
            sql_statement = "UPDATE assets \
                SET quantity = ?, market_value = ? \
                WHERE asset_id = ?"
            sql_params = [self.quantity, self.market_value, self.asset_id]
            sql_update(sql_statement, sql_params)
        self.account.update_investment_worth(self.quantity * self.market_value, change_type)
        print("--------Asset update in DB")

class Liability():
    """Liability Structure matching DB"""
    def __init__(self, liability_id:int=0, account:Account=None, name:str=None, principle:float=0,
                 interest:float=0, interest_rate:float=0, note:str=None):
        self.liability_id = liability_id
        self.account = account
        self.name = name
        self.principle = principle
        self.interest = interest
        self.interest_rate = interest_rate
        self.note = note
        if liability_id == 0:
            self.get_liability_id()

    def get_liability_id(self)->None:
        """Get liability from DB"""
        sql_statement = "SELECT * FROM liabilities WHERE account_id = ? AND name = ?;"
        sql_params = [self.account.account_id, self.name]
        results = sql_get(sql_statement, sql_params)
        if results == []:
            return
        self.liability_id = results[0][0]

    def update_liability(self, change_type:RecordChangeType=None)->None:
        """Update liability in DB"""
        if self.liability_id == 0:
            sql_statement = "INSERT INTO liabilities \
                (account_id, name, principle, interest, interest_rate, note) \
                VALUES (?, ?, ?, ?, ?, ?);"
            sql_params = [self.account.account_id, self.name, self.principle, self.interest,
                          self.interest_rate, self.note]
            self.liability_id = sql_insert(sql_statement, sql_params)
            print("--------Liability added to DB")
        else:
            sql_statement = "UPDATE liabilities \
                SET  \
                WHERE liability_id = ?"
            sql_params = []
            sql_update(sql_statement, sql_params)
        self.account.update_debt_total(0, change_type)
        print("--------Liability update in DB")

class Record:
    """Record Structure matching DB"""
    def __init__(self, record_id:int=0, account:Account=None, asset:Asset=None,
                 liability:Liability=None, amount:float=0, business:str=0, category:str=None,
                 quantity:float=None, change_type:RecordChangeType=None, note:str=0,
                 transaction_date:datetime=None):
        self.record_id = record_id
        self.asset = asset
        self.liability = liability
        self.account = account
        self.amount = amount
        self.business = business
        self.category = category
        self.quantity = quantity
        self.change_type = change_type
        self.note = note
        self.transaction_date = transaction_date

    def get_record_id(self)->None:
        """Get record from DB"""
        sql_statement = "SELECT * FROM records WHERE account_id = ? AND amount = ? AND \
            business = ? AND category = ? AND change_type = ? AND note = ? AND \
            transaction_date = ?;"
        sql_params = [self.account.account_id, self.amount, self.business, self.category,
                      self.change_type.name, self.note, self.transaction_date]
        results = sql_get(sql_statement, sql_params)
        self.record_id = 0 if results == [] else results[0][0]

    def insert_record(self)->None:
        """Insert record into DB"""
        self.get_record_id()
        if self.record_id != 0:
            return
        asset_id, liability_id = None, None
        if self.asset:
            self.asset.update_asset(self.change_type)
            asset_id = self.asset.asset_id
        if self.liability:
            self.liability.update_liability(self.change_type)
            liability_id = self.liability.liability_id
        sql_statement = "INSERT INTO records \
            (account_id, asset_id, liability_id, amount, business, category, quantity, \
            change_type, note, transaction_date) \
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
        sql_params = [self.account.account_id, asset_id, liability_id, self.amount, self.business,
                      self.category, self.quantity, self.change_type.name, self.note,
                      self.transaction_date]
        self.record_id = sql_insert(sql_statement, sql_params)
        self.account.update_cash_funds(self.amount, self.change_type)
        print("--------Record added to DB")

    def get_category(self)->None:
        """Gets the category of the transaction"""
        sql_statement = "SELECT category, change_type FROM records \
            WHERE account_id = ? AND business LIKE ? AND note LIKE ?;"
        results = sql_get(sql_statement, [self.account.account_id, self.business, self.note])
        if results != []:
            self.category = results[0][0]
            self.change_type = RecordChangeType[results[0][1]]
            return

        sql_statement = "SELECT DISTINCT category, change_type FROM records WHERE account_id = ?;"
        categories = sql_get(sql_statement, [self.account.account_id])
        while True:
            try:
                index = 0
                for category, change_type in categories:
                    index += 1
                    print(f"{index}: {category} - {RecordChangeType[change_type].value}")
                print("0: Create new category")
                print(f"${self.amount}: {self.business} - {self.note}")
                user_choice = int(input("Select category - "))
                if user_choice != 0:
                    self.change_type = RecordChangeType[categories[user_choice-1][1]]
                    self.category = categories[user_choice-1][0]
                    break
            except (ValueError, KeyError):
                print("That is not a valid selection")

            try:
                self.category = input("What is the new category name? - ")
                index = 0
                for change_type in RecordChangeType:
                    index += 1
                    print(f"{index}: {change_type.value}")
                user_choice = int(input("Select change type - "))
                self.change_type = RECORD_CHANGE_TYPES[user_choice-1]
                break
            except (ValueError, KeyError):
                print("That is not a valid selection")

def parse_navy_federal_csv(csv_file:str, account:Account)->list[Record]:
    """Parses all transaction info from credit card csv"""
    transactions = []
    with open(csv_file, encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=',')
        next(reader)
        for row in reader:
            transactions.append(Record(
                account=account,
                amount=float(row[2]),
                business=row[10],
                note=row[11],
                transaction_date=datetime.strptime(row[1], "%m/%d/%Y")
            ))
    return transactions

def parse_charles_schwab_investment_csv(csv_file:str, account:Account)->list[Record]:
    """Parses all transaction info from charles swab csv"""
    transactions = []
    with open(csv_file, encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=',')
        next(reader)
        for row in reader:
            record = Record(
                account=account,
                amount=abs(float(row[7].replace("$", ""))),
                business=row[1],
                note=f"{row[3]} {row[2]}",
                transaction_date=datetime.strptime(row[0][:10], "%m/%d/%Y")
            )
            if "Buy" == row[1] or "Reinvest Shares" == row[1]:
                print(f"Buying {row[3]} {row[2]}")
                record.asset = Asset(
                    account=account,
                )
            elif "Sell" == row[1]:
                print(f"Selling {row[3]} {row[2]}")
                record.asset = Asset(
                    account=account,
                )
            transactions.append(record)
    return transactions

def parse_charles_schwab_checking_csv(csv_file:str, account:Account)->list[Record]:
    """Parses all transaction info from charles swab csv"""
    transactions = []
    with open(csv_file, encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=',')
        next(reader)
        for row in reader:
            if "Posted" not in row[1]:
                continue
            amount = float((row[6][1:] if row[6] != "" else row[5][1:]).replace(",", ""))
            transactions.append(Record(
                account=account,
                amount=amount,
                business=row[4],
                note=row[2],
                transaction_date=datetime.strptime(row[0], "%m/%d/%Y")
            ))
    return transactions

def get_account()->Account:
    """Get account id from account name"""
    sql_statement = "SELECT * FROM accounts;"
    accounts = sql_get(sql_statement, [])
    choice = 0
    while True:
        index = 0
        for _, _, name, _, _, _, _ in accounts:
            index += 1
            print(f"{index}: {name}")
        choice = input("Which account - ")
        if 0 < int(choice) and int(choice) <= index:
            break
    return Account(account_id=accounts[int(choice)-1][0])

def main()->None:
    """Main Driver"""
    parser = argparse.ArgumentParser(description="Insert PDF and CSV data")
    parser.add_argument("-b", "--book", help='Book ID', required=False)
    parser.add_argument("-f", "--file", help='Transaction File Name', required=True)
    parser.add_argument("-i", "--institute", help='Institute of the transactions', required=True)
    args = parser.parse_args()
    load_dotenv()
    account = get_account()
    transactions = []
    if (SupportedInstitute[args.institute] == SupportedInstitute.NAVY_FEDERAL
            and ".csv" in args.file):
        transactions = parse_navy_federal_csv(args.file, account)
    elif SupportedInstitute[args.institute] == SupportedInstitute.CHARLES_SCHWAB:
        if "Checking" in args.file:
            transactions = parse_charles_schwab_checking_csv(args.file, account)
        elif "Individual" in args.file or "Roth" in args.file:
            transactions = parse_charles_schwab_investment_csv(args.file, account)
    else:
        print("Not a valid File")
        sys.exit()

    for record in reversed(transactions):
        record:Record
        record.get_category()
        record.insert_record()

if __name__ == "__main__":
    main()
