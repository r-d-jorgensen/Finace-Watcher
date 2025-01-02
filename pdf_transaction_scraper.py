"""Scrapes All Bank transactions from PDF File and inserts into DB"""
import sys
import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from pypdf import PdfReader
sqlite3.register_adapter(datetime, lambda dt: dt.strftime("%Y-%m-%d"))

class NoData(Exception):
    """Error is raised when no data is retrived from system"""
    def __init__(self, message="Data Not pulled correctly"):
        super().__init__(message)

def parse_navy_federal_pdf(pdf_file:str)->tuple:
    """Parses all transaction info from pdf"""
    transactions = ([], [])
    reader = PdfReader(pdf_file)
    debits_found, credits_found = False, False

    start_of_debits = "Trans Date Post Date Reference No. Description Submitted By Amount"
    end_of_debits = "TOTAL PAYMENTS AND CREDITS"

    start_of_credits = "Trans Date Post Date Reference No."
    end_of_credits = f"TOTAL New Activity for {os.getenv("LEGAL_NAME")}"
    for page in reader.pages[1:]:
        text = page.extract_text().split("\n")
        for line in text:
            if end_of_debits in line:
                debits_found = False
            elif end_of_credits in line:
                return transactions

            if start_of_debits in line:
                debits_found = True
            elif start_of_credits in line:
                credits_found = True
            elif debits_found:
                # TODO: debits should be parsed here
                transactions[0].append(line)
            elif credits_found:
                if "TRANSACTIONS" in line:
                    continue
                if "Page " in line:
                    continue
                if os.getenv("LEGAL_NAME") in line:
                    continue

                data_point = parse_transaction_line(line)
                transactions[1].append(data_point)
    raise NoData()

def parse_transaction_line(data_line:str)->list:
    """Takes pdf str and returns transaction record"""
    holder = ""
    consumed = 0
    data_point = [0, 0, 0.0, "", "", "", datetime]
    for char in data_line:
        if (char == " " and consumed < 3) or char == "$":
            if consumed == 0:
                data_point[6] = datetime.strptime(holder[:6] + "20" + holder[6:], "%m/%d/%Y")
            elif consumed == 3:
                data_point[3] = holder[:25].strip()
                data_point[4] = holder[25:]
            holder = ""
            consumed += 1
        else:
            holder += char
    data_point[2] = float(holder.replace(",", ""))
    return data_point

def get_category(book_id:int, amount:float, business:str, location:str, trasaction_date:datetime)->int:
    """Gets the category of the transaction"""
    try:
        sql_statment = "SELECT category_id FROM records WHERE bank_account_id = ? AND business LIKE ?;"
        category_id = sql_get(sql_statment, [book_id, business])[0][0]
    except IndexError:
        sql_statment = "SELECT * FROM categories WHERE book_id = ?;"
        categories = sql_get(sql_statment, [book_id])
        category_id = None
        while category_id is None:
            print("---------------------------------------------------------------")
            for category in categories:
                print(f"{category[0]}: {category[2]}")
            print("0: None of the Above")
            try:
                print(f"${amount} from '{business}' located at '{location.strip()}' on {trasaction_date.date()}")
                category_id = int(input("Select the category that best describes the above record - "))
            except ValueError:
                print("The value inputed is not a intiger")
        if category_id == 0:
            category_name = input("What is the name of the new category? - ")
            sql_statment = "INSERT INTO categories (book_id, name) VALUES (?, ?);"
            category_id = sql_insert(sql_statment, [book_id, category_name])
    return category_id

def sql_get(sql_statment:str, sql_paramiters:list)->list:
    """Gets data from sql db"""
    rows = []
    try:
        db_connection = sqlite3.connect("finance.db")
        cursor = db_connection.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')
        cursor.execute(sql_statment, sql_paramiters)
        rows = cursor.fetchall()
        db_connection.commit()
        db_connection.close()
    except sqlite3.Error as error:
        print("Data was not retrived from DB")
        print(error)
        print(sql_statment)
        print(sql_paramiters)
    return rows

def sql_insert(sql_statment:str, sql_paramiters:list)->int:
    """Inserts single row into sql db and returns id"""
    insert_id = 0
    try:
        db_connection = sqlite3.connect("finance.db")
        cursor = db_connection.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')
        cursor.execute(sql_statment, sql_paramiters)
        insert_id = cursor.lastrowid
        db_connection.commit()
        db_connection.close()
    except sqlite3.Error as error:
        print("Data was not inserted into DB")
        print(error)
        print(sql_statment)
        print(sql_paramiters)
    return insert_id

def load_pdf_data(book_id:int, bank_account_id:int, pdf_file:str)->None:
    """Driver function of script"""
    sql_check_statment = "SELECT * FROM records WHERE bank_account_id = ? AND category_id = ? AND \
        amount = ? AND business = ? AND location = ? AND note = ? AND transaction_date = ?;"
    sql_insert_statment = "INSERT INTO records \
            (bank_account_id, category_id, amount, business, location, note, transaction_date) \
            VALUES (?, ?, ?, ?, ?, ?, ?);"

    _, transaction_credits = parse_navy_federal_pdf(pdf_file)
    for record in transaction_credits:
        record[0] = bank_account_id
        record[1] = get_category(book_id, record[2], record[3], record[4], record[6])
        if len(sql_get(sql_check_statment, record)) == 0:
            sql_insert(sql_insert_statment, record)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py pdf_file")
        sys.exit()
    else:
        pdf_arg = sys.argv[1]
    load_dotenv()
    load_pdf_data(1, 1, pdf_arg)
