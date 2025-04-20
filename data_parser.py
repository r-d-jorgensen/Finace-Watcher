"""Different Data Parsers and a general flow mechanism"""
import csv
import sys
from enum import Enum
from datetime import datetime
from db_classes import Record, Account, Asset

class SupportedInstitute(Enum):
    """Supported Institute with Parsing"""
    NAVY_FEDERAL = "Navy Federal"
    CHARLES_SCHWAB = "Charles Schwab"
    T_ROWE_PRICE = "T Rowe Price"


def strip_financial_markers(amount_string:str)->float:
    """Remove currency makers, symbols and commas"""
    return abs(float(
        amount_string
        .replace("$", "")
        .replace("", "")
    ))

def parse_t_rowe_price_401k_csv(csv_file:str, account:Account)->list[Record]:
    """Parses all transaction info from T Rowe Price for 401k data"""
    transactions = []
    with open(csv_file, encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=',')
        next(reader) # must burn 4 rows for dead row values
        next(reader)
        next(reader)
        next(reader)
        for row in reader:
            transfer_in_record = None
            activity_type = row[1].strip()
            if activity_type in "Market Fluctuation":
                continue
            if activity_type in "Fee":
                if row[4][1] != '-':
                    activity_type = "Rebate"
                else:
                    print(row)
                    print("Handle Fee Event -No data Right now")
                    sys.exit()

            if activity_type in ("Contribution", "Rebate"):
                transfer_in_record = Record(
                    account=account,
                    amount=strip_financial_markers(row[4]),
                    business=row[3],
                    note=f"{activity_type} to account",
                    transaction_date=datetime.strptime(row[0], "%m/%d/%Y")
                )
                activity_type = "Exchange In"

            record = Record(
                account=account,
                amount=strip_financial_markers(row[4]),
                business=row[3],
                note=f"{activity_type} {row[2]}",
                transaction_date=datetime.strptime(row[0], "%m/%d/%Y")
            )
            if activity_type in ("Exchange Out", "Exchange In"):
                record.add_changed_asset(Asset(
                    account=account,
                    asset= row[2],
                    quantity= float(row[5]),
                    market_value= strip_financial_markers(row[6]),
                    note= row[3]
                ))
            transactions.append(record)
            if transfer_in_record:
                transactions.append(transfer_in_record)
    return transactions

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
            if row[7] == "":
                continue
            record = Record(
                account=account,
                amount=abs(float(row[7].replace("$", ""))),
                business=row[1],
                note=f"{row[3]} {row[2]}",
                transaction_date=datetime.strptime(row[0][:10], "%m/%d/%Y")
            )
            if "Buy" == row[1] or "Reinvest Shares" == row[1] or "Sell" == row[1]:
                record.add_changed_asset(Asset(
                    account=account,
                    asset= row[3],
                    quantity= float(row[4]),
                    market_value= float(row[5][1:]),
                    note= row[2]
                ))
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

def data_parser(account:Account, institute:str, file:str)->list[Record]:
    """Main Flow data Parser"""
    if (SupportedInstitute[institute] == SupportedInstitute.NAVY_FEDERAL
            and ".csv" in file):
        return parse_navy_federal_csv(file, account)
    if SupportedInstitute[institute] == SupportedInstitute.CHARLES_SCHWAB:
        if "Checking" in file:
            return parse_charles_schwab_checking_csv(file, account)
        if "Individual" in file or "Roth" in file:
            return parse_charles_schwab_investment_csv(file, account)
    if (SupportedInstitute[institute] == SupportedInstitute.T_ROWE_PRICE
            and ".csv" in file):
        return parse_t_rowe_price_401k_csv(file, account)
    print("Not a valid File")
    sys.exit()
