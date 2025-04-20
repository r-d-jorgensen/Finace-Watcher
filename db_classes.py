"""Database Classes, structures and helpers"""
import sys
from enum import Enum
from datetime import datetime
from db_helper import sql_get, sql_insert, sql_update

class RecordChangeType(Enum):
    """Types of changes that records embody"""
    CREDIT_ACCOUNT = "Credit Account"
    DEBIT_ACCOUNT = "Debit Account"
    BUY_ASSET = "Buy Asset"
    SELL_ASSET = "Sell Asset"

RECORD_CHANGE_TYPES = [change_type for change_type in RecordChangeType]

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
        if change_type in (RecordChangeType.DEBIT_ACCOUNT, RecordChangeType.SELL_ASSET):
            self.cash_funds += amount
        elif change_type in (RecordChangeType.CREDIT_ACCOUNT, RecordChangeType.BUY_ASSET):
            self.cash_funds -= amount
        else:
            print("Not a supported record change type", amount, change_type.name)
            sys.exit()

        sql_statement = "UPDATE accounts \
            SET cash_funds = ? \
            WHERE account_id = ?"
        sql_params = [round(self.cash_funds, 2), self.account_id]
        sql_update(sql_statement, sql_params)

    def update_investment_worth(self, asset_value_change:float)->None:
        """Update total investment counter"""
        self.investment_worth += asset_value_change

        sql_statement = "UPDATE accounts \
            SET investment_worth = ? \
            WHERE account_id = ?"
        sql_params = [round(self.investment_worth, 2), self.account_id]
        sql_update(sql_statement, sql_params)

    def update_debt_total(self, amount:float, change_type:RecordChangeType)->None:
        """Update total debt counter"""
        print("Not a supported record change type", amount, change_type.name)
        sys.exit()

class Asset:
    """Asset Structure matching DB"""
    def __init__(self, asset_id:int=None, account:Account=None, asset:str=None, quantity:float=0,
                 market_value:float=0, note:str=None):
        self.asset_id = asset_id
        self.account = account
        self.asset = asset
        self.quantity = quantity
        self.market_value = market_value
        self.note = note

    def get_asset_id(self)->None:
        """Get asset from DB"""
        sql_statement = "SELECT asset_id FROM assets WHERE account_id = ? AND asset LIKE ?;"
        sql_params = [self.account.account_id, f"%{self.asset}%"]
        results = sql_get(sql_statement, sql_params)
        self.asset_id = None if results == [] else results[0][0]

    def get_asset_values(self)->None:
        """Get asset values from DB"""
        sql_statement = "SELECT * FROM assets WHERE asset_id = ?;"
        sql_params = [self.asset_id]
        results = sql_get(sql_statement, sql_params)
        self.asset = None if results == [] else results[0][2]
        self.quantity = None if results == [] else results[0][3]
        self.market_value = None if results == [] else results[0][4]

    def insert_asset(self)->None:
        """Insert New asset into DB"""
        if self.asset_id is not None:
            print("System error, asset exists cannot insert should update")
            sys.exit()
        sql_statement = "INSERT INTO assets \
            (account_id, asset, quantity, market_value, note) \
            VALUES (?, ?, ?, ?, ?);"
        sql_params = [self.account.account_id, self.asset, self.quantity, self.market_value,
                      self.note]
        self.asset_id = sql_insert(sql_statement, sql_params)
        self.account.update_investment_worth(self.quantity * self.market_value)
        print("--------New Asset added to DB")

    def update_asset(self, change_type:RecordChangeType)->None:
        """Update asset in DB"""
        self.get_asset_id()
        if self.asset_id is None:
            self.insert_asset()
            return
        quantity_change = self.quantity
        current_market_value = self.market_value
        if change_type == RecordChangeType.SELL_ASSET:
            quantity_change = -quantity_change

        self.get_asset_values()
        old_total_asset_value = self.quantity * self.market_value
        self.quantity += quantity_change
        self.market_value = current_market_value
        asset_value_change = self.quantity * self.market_value - old_total_asset_value

        sql_statement = "UPDATE assets \
            SET quantity = ?, market_value = ? \
            WHERE asset_id = ?"
        sql_params = [self.quantity, self.market_value, self.asset_id]
        sql_update(sql_statement, sql_params)
        self.account.update_investment_worth(asset_value_change)
        print("--------Updated Asset in DB")

class Liability:
    """Liability Structure matching DB"""
    def __init__(self, liability_id:int=None, account:Account=None, name:str=None,
                 principle:float=0, interest:float=0, interest_rate:float=0, note:str=None):
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
        self.liability_id = None if results == [] else results[0][0]

    def update_liability(self, change_type:RecordChangeType=None)->None:
        """Update liability in DB"""
        print(change_type, "Function not implemented")
        sys.exit()
        # if self.liability_id is None:
        #     sql_statement = "INSERT INTO liabilities \
        #         (account_id, name, principle, interest, interest_rate, note) \
        #         VALUES (?, ?, ?, ?, ?, ?);"
        #     sql_params = [self.account.account_id, self.name, self.principle, self.interest,
        #                   self.interest_rate, self.note]
        #     self.liability_id = sql_insert(sql_statement, sql_params)
        #     print("--------Liability added to DB")
        # else:
        #     sql_statement = "UPDATE liabilities \
        #         SET  \
        #         WHERE liability_id = ?"
        #     sql_params = []
        #     sql_update(sql_statement, sql_params)
        # self.account.update_debt_total(0, change_type)
        # print("--------Liability update in DB")

class Record:
    """Record Structure matching DB"""
    def __init__(self, record_id:int=None, account:Account=None, changed_asset:Asset=Asset(),
                 changed_liability:Liability=Liability(), amount:float=0, business:str=0,
                 category:str=None, change_type:RecordChangeType=None, note:str=0,
                 transaction_date:datetime=None):
        self.record_id = record_id
        self.changed_asset = changed_asset
        self.changed_liability = changed_liability
        self.account = account
        self.amount = amount
        self.business = business
        self.category = category
        self.quantity = changed_asset.quantity if changed_asset else None
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
        self.record_id = None if results == [] else results[0][0]

    def insert_record(self)->None:
        """Insert record into DB"""
        self.get_record_id()
        if self.record_id is not None:
            return
        if self.changed_asset.account:
            self.changed_asset.update_asset(self.change_type)
        if self.changed_liability.account:
            self.changed_liability.update_liability(self.change_type)
        sql_statement = "INSERT INTO records \
            (account_id, asset_id, liability_id, amount, business, category, quantity, \
            change_type, note, transaction_date) \
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
        sql_params = [self.account.account_id, self.changed_asset.asset_id,
                      self.changed_liability.liability_id, self.amount, self.business,
                      self.category, self.quantity, self.change_type.name,
                      self.note, self.transaction_date]
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
                print(self.transaction_date.date() +
                      F" ${self.amount}: {self.business} - {self.note}")
                user_choice = int(input("Select category - "))
                if user_choice == 0:
                    break
                if 0 < user_choice < len(categories)+1:
                    self.change_type = RecordChangeType[categories[user_choice-1][1]]
                    self.category = categories[user_choice-1][0]
                    return
            except (ValueError, KeyError):
                print("That is not a valid selection")

        while True:
            try:
                self.category = input("What is the new category name? - ")
                index = 0
                for change_type in RecordChangeType:
                    index += 1
                    print(f"{index}: {change_type.value}")
                user_choice = int(input("Select change type - "))
                self.change_type = RECORD_CHANGE_TYPES[user_choice-1]
                return
            except (ValueError, KeyError):
                print("That is not a valid selection")

    def add_changed_asset(self, changed_asset:Asset)->None:
        """Add an asset to the existing record"""
        self.changed_asset = changed_asset
        self.quantity = changed_asset.quantity if changed_asset else None

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
