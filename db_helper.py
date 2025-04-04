"""Helper file for DB interactions"""
import os
import sys
import sqlite3
from datetime import datetime
sqlite3.register_adapter(datetime, lambda dt: dt.strftime("%Y-%m-%d"))

def sql_get(sql_statement:str, sql_parameters:list)->list:
    """Gets data from sql db"""
    rows = []
    try:
        db_connection = sqlite3.connect(os.getenv("DB_NAME"))
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
        db_connection = sqlite3.connect(os.getenv("DB_NAME"))
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
        sys.exit()
    return insert_id

def sql_update(sql_statement:str, sql_parameters:list)->None:
    """Updates sql db"""
    try:
        db_connection = sqlite3.connect(os.getenv("DB_NAME"))
        cursor = db_connection.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')
        cursor.execute(sql_statement, sql_parameters)
        db_connection.commit()
        db_connection.close()
    except sqlite3.Error as error:
        print("Data was not inserted into DB")
        print(error)
        print(sql_statement)
        print(sql_parameters)
        sys.exit()
