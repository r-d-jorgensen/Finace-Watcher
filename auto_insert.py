"""Scrapes All Bank transactions from PDF File and inserts into DB"""
import os
import shutil
import argparse
from dotenv import load_dotenv
from data_parser import data_parser
from db_classes import get_account

def main()->None:
    """Main Driver"""
    parser = argparse.ArgumentParser(description="Insert PDF and CSV data")
    parser.add_argument("-b", "--book", help='Book ID', required=False)
    parser.add_argument("-f", "--file", help='Transaction File Name', required=True)
    parser.add_argument("-i", "--institute", help='Institute of the transactions', required=True)
    args = parser.parse_args()
    load_dotenv()
    account = get_account()
    transactions = data_parser(account, args.institute, args.file)

    for record in reversed(transactions):
        record.get_category()
        record.insert_record()

    last_record = transactions[0]
    name, ext = os.path.splitext(args.file)
    new_filename = f"{name}-{last_record.transaction_date.date()}{ext}"
    destination = os.path.join("historic", new_filename)
    shutil.copy(args.file, destination)
    os.remove(args.file)

if __name__ == "__main__":
    main()
