"""Insert row into DB manually"""
import sqlite3
import argparse
from enum import Enum
from dotenv import load_dotenv

class Tables(Enum):
    """Tables within DB"""
    BOOK = "Book"
    ACCOUNT = "Account"
    RECORD = "Record"

def book_insert(args):
    """Insert Book into DB"""

def account_insert(args):
    """Insert Account into DB"""

def record_insert(args):
    """Insert Record into DB"""

def selector(args, table:str):
    """Select the inserter required for the table"""
    if table == Tables.BOOK:
        book_insert(args)
    elif table == Tables.ACCOUNT:
        account_insert(args)
    elif table == Tables.RECORD:
        record_insert(args)
    else:
        print(f"No table matching {table}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Insert PDF and CSV data")
    parser.add_argument("-t", "--table", help='Table Name', required=True)
    args = parser.parse_args()
    load_dotenv()
    selector(args, args.table)
