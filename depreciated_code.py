"""Old code that could be useful but is currently not"""
import os
import re
from datetime import datetime
from pypdf import PdfReader

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
                    print("INSERT INTO records (account_id, category_id, \
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
