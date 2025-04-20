"""Scrapes All Bank transactions from PDF File and inserts into DB"""
import argparse
from dotenv import load_dotenv
from data_parser import data_parser
from db_classes import Record, get_account

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
        record:Record
        record.get_category()
        record.insert_record()

if __name__ == "__main__":
    main()
