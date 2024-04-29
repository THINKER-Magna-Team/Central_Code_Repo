# -*- coding: utf-8 -*-
"""
Created on Sat Feb 24 15:53:22 2024

@author: Luke Vickers
"""
import sqlite3
import pandas as pd
import serial as ser
import csv
from datetime import datetime
import os
import numpy as np
import time




# disconnect from db at end of script? (T/F)
disconnect = True

# create new tables for new db? (T/F)
# if youre getting new rows being created after rerunning the code, turn off new_db
new_db = True

USB_PORT_ONE = "/dev/ttyACM0"  #Serial Port for Arduino 1-Need to run 'ls /dev/tty* to find connected arduinos
BAUD_RATE = 115200
def init_USB_connection(USB_PORT,BAUD_RATE):
    rfid_data = {'UID': [],'Location': []}  #Creates dictionary to use to create dataframe
    rfid_df = pd.DataFrame(rfid_data)  #Creates dataframe from aforemention dictionary
    ser_n = ser.Serial(USB_PORT, BAUD_RATE, timeout=1)  #Creates ser_one object for first arduino
    ser_n.reset_input_buffer()  #Resets input buffer to prevent lingering signals
    return (rfid_data,rfid_df,ser_n)

(rfid_data,rfid_df,ser_one) = init_USB_connection(USB_PORT_ONE,BAUD_RATE)


# Importing fake data set
'''
with open('MultireaderToSQLWindowsForkliftDataset.txt', 'r') as f: #Set f as a shortcut to open the file and set it to read mode
    dataset = csv.reader(f) #Create a new dataset variable in python with the data from the file
    dataset = np.array(list(dataset)) #Turn the dataset variable into a list and then into a numpy array
'''
# connection.close to allow file to be deleted


# This file should write the input data type into the sql database with the following headings


# connecting to database
current_directory = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_directory, 'RFIDForklifttest.db')
print(db_path)
connection = sqlite3.connect(db_path)
cursor = connection.cursor()


# loc, tag UID, time
# tag UID, item description

"""creating both tables, in this it will be assummed that BayDescription is
created first when the user tags a new box. With this, a new line will not be
able to be made in BayInventory until it has been marked in BayDescription ideally."""

# the line below ensures the UID is found in BayDescription before it can be inserted into BayInventory
# This should be set to ON if we want to enforce foreign keys!!
cursor.execute("PRAGMA foreign_keys = OFF;")


def create_table():
    cursor.execute(""" CREATE TABLE IF NOT EXISTS PalletLastScanned (
        palletUID TEXT,
        palletLastScannedTime TEXT
                   
);
    """)
    cursor.execute(f"INSERT OR IGNORE INTO PalletLastScanned VALUES ('0','0');")


    cursor.execute(""" CREATE TABLE IF NOT EXISTS ShelfLastScanned (
        shelfUID TEXT,
        shelfLastScannedTime TEXT);
    """)


    cursor.execute(f"INSERT OR IGNORE INTO ShelfLastScanned VALUES ('0','0');")    

    cursor.execute("""
     CREATE TABLE IF NOT EXISTS CurrentInventory (
        shelfUID  PRIMARY KEY,
        palletUID TEXT,
        timestep DATETIME)
    """)
   
    connection.commit()
    print('Tables created')


if new_db == True:
    create_table()


connection.commit()


def decodeSerial(SerialString):

    current_tag = ''
    current_uid = ''
    current_time = ''
    last_pallet_uid = ''
    last_pallet_time = ''
    last_shelf_uid = ''
    last_shelf_time = ''

    parts = SerialString.split('|||')
    for part in parts:
        if 'Current Tag' in part:
            tag_info = part.split('class: ')[1].split(' UID: ')
            current_tag = tag_info[0]
            current_uid = tag_info[1].split(' at time: ')[0]
            current_time = tag_info[1].split(' at time: ')[1].strip()
            print(f"The current tag UID is: {current_uid}")
        
        if 'Last Pallet' in part:
            current_directory = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(current_directory, 'RFIDForklifttest.db')
            connection = sqlite3.connect(db_path)
            cursor = connection.cursor()
            last_pallet_info = part.split('- UID: ')
            last_pallet_uid = last_pallet_info[1].split(' time since scan: ')[0].strip()
            if last_pallet_uid =='':
                query = cursor.execute("SELECT palletUID FROM PalletLastScanned")
                last_pallet_uid = cursor.fetchone()
                last_pallet_uid = last_pallet_uid[0].lstrip("('").rstrip("',)")

            last_pallet_time = last_pallet_info[1].split(' time since scan: ')[1].strip()
        if 'Last Shelf' in part:
            current_directory = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(current_directory, 'RFIDForklifttest.db')
            connection = sqlite3.connect(db_path)
            cursor = connection.cursor()
            last_shelf_info = part.split('- UID: ')
            last_shelf_uid = last_shelf_info[1].split(' time since scan: ')[0].strip()
            if last_shelf_uid =='':
                print("no shelf scanned yet")
                query = cursor.execute("SELECT shelfUID FROM ShelfLastScanned")
                last_shelf_uid = str(cursor.fetchone())
                last_shelf_uid = last_shelf_uid
                last_shelf_uid = last_shelf_uid[0].lstrip("('").rstrip("',)")

            last_shelf_time = last_shelf_info[1].split(' time since scan: ')[1].strip().rstrip("']")
        params = [current_tag,current_uid,current_time,last_pallet_uid,last_pallet_time,last_shelf_uid,last_shelf_time]
    return params

def UpdateTable(table,last_uid,last_time):
    current_directory = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_directory, 'RFIDForklifttest.db')
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute(f"UPDATE {table}LastScanned SET {table.lower()}LastScannedTime = (?), {table.lower()}UID = ?", (str(last_time),str(last_uid)))
    connection.commit()
    currenttime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Class: {table} UID: {last_uid} updated as last scanned {table.lower()} at {currenttime}")

    '''
    try:
        cursor.execute(
            f"INSERT INTO {table}LastScanned VALUES (?,?) ON DUPLICATE KEY UPDATE {table}LastScannedTime = ?,{table.lower}UID = ? ",(last_uid,last_time,last_uid,last_time))
        connection.commit()
        print(f'{table} Data inserted')
    except sqlite3.IntegrityError:
        cursor.execute(
            f"UPDATE {table}LastScanned SET {table}LastScannedTime = (?), {table.lower}UID = ?", (last_time,last_uid))
        connection.commit()
        print(f'{table} Data Updated')
    except Exception as e:
        print('Error',str(e))
    '''

def UpdateSQL(params):
    
     # targetTable, location, UID, and time
    
    current_tag = params[0]
    current_uid = params[1]
    current_time = params[2]
    last_pallet_uid = params[3]
    last_pallet_time = params[4]
    last_shelf_uid = params[5]
    last_shelf_time = params[6]

    #Updating pallet
    UpdateTable('Pallet',last_pallet_uid,last_pallet_time)
    #Updating shelf
    UpdateTable('Shelf',last_shelf_uid,last_shelf_time)
'''
    # Updating pallet
    try:
        cursor.execute(
            f"INSERT INTO PalletLastScanned VALUES (?,?)", (last_pallet_uid,last_pallet_time))
        connection.commit()
        print('Data inserted')
    except sqlite3.IntegrityError:
        cursor.execute(
            f"UPDATE PalletLastScanned SET PalletLastScanned = (?), palletUID = ?",(last_pallet_time,last_pallet_uid))
        connection.commit()
        print('Data Updated')
    except Exception as e:
        print('Error',str(e))
    # Updating shelf
    try:
        cursor.execute(
            f"INSERT INTO ShelfLastScanned VALUES (?,?)",(last_shelf_uid,last_shelf_time))
        connection.commit()
        print('Data inserted')
    except sqlite3.IntegrityError:
        cursor.execute(
            f"UPDATE ShelfLastScanned SET ShelfLastScanned = (?), shelfUID = ?", (last_shelf_time,last_shelf_uid))
        connection.commit()
        print('Data Updated')
    except Exception as e:
        print('Error',str(e))
    '''

while True:
    current_directory = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_directory, 'RFIDForklifttest.db')
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    if ser_one.in_waiting > 0:
        
        line = ser_one.readline().decode('UTF-8').rstrip()
        if line != "Bad CRC":
            

            params = decodeSerial(str(line))
            #print(params)

            current_tag = params[0]
            current_uid = params[1]
            current_time = params[2]
            last_pallet_uid = params[3]
            last_pallet_time = params[4]
            last_shelf_uid = params[5]
            last_shelf_time = params[6]

            currenttime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            #send_data('BayInventory',location,UID,time)
            #print(f"UID: {UID} placed into bay {location} at {currenttime}")
            UpdateSQL(params)
        else:
            print("Partial Scan, skipping")

        if disconnect:
            current_directory = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(current_directory, 'RFIDForklifttest.db')
            connection = sqlite3.connect(db_path)
            cursor = connection.cursor()
            #connection.commit()
            #if connection.is_connected():
            cursor.close()
            connection.close()
            print('Connection Disconnected')
        time.sleep(1)
        #print("taking a nap")
