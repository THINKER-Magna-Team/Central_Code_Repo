import mysql.connector
import csv
from datetime import datetime
import os
import numpy as np
import time
import pandas as pd
import serial as ser
import sys






# disconnect from db at end of script? (T/F)
disconnect = True

# create new tables for new db? (T/F)
# if youre getting new rows being created after rerunning the code, turn off new_db
new_db = False


# Connection parameters for MySQL
hostname = "Server_Hostanme"
database = "Database"
port = "Port"
username = "Username"
password = "Password"


# For Luke's local DB



# Create connection to MySQL database
try:
    connection = mysql.connector.connect(host=hostname, database=database, auth_plugin='mysql_native_password', user=username, password=password, port=port)
except:
    print("DB asleep")
    sys.exit(1)
cursor = connection.cursor()
cursor.execute("select database();")
record = cursor.fetchone()
print("You're connected to database: ", record)


USB_PORT_ONE = "/dev/ttyACM0"  #Serial Port for Arduino 1-Need to run 'ls /dev/tty* to find connected arduinos
BAUD_RATE = 115200
def init_USB_connection(USB_PORT,BAUD_RATE):
    rfid_data = {'UID': [],'Location': []}  #Creates dictionary to use to create dataframe
    rfid_df = pd.DataFrame(rfid_data)  #Creates dataframe from aforementioned dictionary
    ser_n = ser.Serial(USB_PORT, BAUD_RATE, timeout=1)  #Creates ser_one object for first arduino
    ser_n.reset_input_buffer()  #Resets input buffer to prevent lingering signals
    return (rfid_data,rfid_df,ser_n)

(rfid_data,rfid_df,ser_one) = init_USB_connection(USB_PORT_ONE,BAUD_RATE)



# Create tables if they do not exist
def create_table():
    cursor.execute("""CREATE TABLE IF NOT EXISTS PalletLastScanned (
        palletUID VARCHAR(255),
        palletLastScannedTime VARCHAR(255)
    )""")
    cursor.execute("INSERT IGNORE INTO PalletLastScanned VALUES ('0', '0')")

    cursor.execute("""CREATE TABLE IF NOT EXISTS ShelfLastScanned (
        shelfUID VARCHAR(255),
        shelfLastScannedTime VARCHAR(255)
    )""")
    cursor.execute("INSERT IGNORE INTO ShelfLastScanned VALUES ('0', '0')")

    cursor.execute("""CREATE TABLE IF NOT EXISTS ItemLocations (
        shelfUID VARCHAR(255) PRIMARY KEY,
        palletUID VARCHAR(255),
        timestamp DATETIME
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS CompleteInventory (
        palletUID VARCHAR(255) PRIMARY KEY,
        SKU VARCHAR(255),
        Quantity INT,
        Description VARCHAR(255)
    )""")

    connection.commit()
    print('Tables created')


if new_db == True:
    create_table()

if connection.is_connected():
    cursor.close()
    connection.close()

"""
# Importing fake data set
with open('MultireaderToSQLWindowsForkliftDataset.txt', 'r') as f:
    dataset = csv.reader(f)
    dataset = np.array(list(dataset))
"""
def decodeSerial(SerialString):
    current_tag = ''
    current_uid = ''
    current_time = ''
    last_pallet_uid = ''
    last_pallet_time = ''
    last_shelf_uid = ''
    last_shelf_time = ''
    dropoff_mode = ''

    parts = SerialString.split('|||')
    for part in parts:
        if 'Forklift Mode' in part:
            dropoff_mode = part.split(':')[1].strip()
        if 'Current Tag' in part:
            tag_info = part.split('class: ')[1].split(' UID: ')
            current_tag = tag_info[0]
            current_uid = tag_info[1].split(' at time: ')[0]
            current_time = tag_info[1].split(' at time: ')[1].strip()

        if 'Last Pallet' in part:
            connection = mysql.connector.connect(host=hostname, database=database, auth_plugin='mysql_native_password', user=username, password=password, port=port)
            cursor = connection.cursor()
            last_pallet_info = part.split('- UID: ')
            last_pallet_uid = last_pallet_info[1].split(' time since scan: ')[0].strip()
            if last_pallet_uid =='':
                query = cursor.execute("SELECT palletUID FROM PalletLastScanned")
                last_pallet_uid = (cursor.fetchone())
                last_pallet_uid = last_pallet_uid[0]
                if isinstance(last_pallet_uid,bytearray):
                    last_pallet_uid = last_pallet_uid.decode()
                last_pallet_uid = str(last_pallet_uid)
                # sometimes if there is multiple rows this returns tuple, only want first
                last_pallet_uid = last_pallet_uid.lstrip("('").rstrip("',)")
            if connection.is_connected():
                cursor.close()
                connection.close()

            last_pallet_time = last_pallet_info[1].split(' time since scan: ')[1].strip()

        if 'Last Shelf' in part:
            connection = mysql.connector.connect(host=hostname, database=database, auth_plugin='mysql_native_password', user=username, password=password, port=port)
            cursor = connection.cursor()
            last_shelf_info = part.split('- UID: ')
            last_shelf_uid = last_shelf_info[1].split(' time since scan: ')[0].strip()
            if last_shelf_uid =='':
                query = cursor.execute("SELECT shelfUID FROM ShelfLastScanned")
                last_shelf_uid = (cursor.fetchone())
                last_shelf_uid = last_shelf_uid[0]
                if isinstance(last_shelf_uid,bytearray):
                    last_shelf_uid = last_shelf_uid.decode()
                last_shelf_uid = str(last_shelf_uid)
                last_shelf_uid = last_shelf_uid.lstrip("('").rstrip("',)")
            if connection.is_connected():
                cursor.close()
                connection.close()

            last_shelf_time = last_shelf_info[1].split(' time since scan: ')[1].strip().rstrip("']")

        params = [current_tag,current_uid,current_time,last_pallet_uid,last_pallet_time,last_shelf_uid,last_shelf_time,dropoff_mode]
    return params

def UpdateTable(table,last_uid1,last_uid2,switch):
    connection = mysql.connector.connect(host=hostname, database=database, auth_plugin='mysql_native_password', user=username, password=password, port=port)
    currenttime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor = connection.cursor()
    if table == 'Pallet' or table == 'Shelf':
        cursor.execute(f"UPDATE {table}LastScanned SET {table.lower()}LastScannedTime = %s, {table.lower()}UID = %s",
                   (str(currenttime), str(last_uid1)))
        connection.commit()
        print(f"Class: {table} UID: {last_uid1} updated as last scanned {table.lower()} at {currenttime}")
    if table == 'ItemLocations':

        if switch == 'P':
            cursor.execute(f"SELECT shelfUID,palletUID FROM ItemLocations WHERE palletUID = %s",(last_uid1,))
            rows = cursor.fetchall()

# If rows are returned, print them

            '''
            after pickup, check all inventory for the pallet id except forklift, and overwrite all
            other locations to empty if it contains the pallet id


            before dropoff, check if any item is there before adding new item
            after dropoff, assign pallet to new location and remove the pallet from all other locations
            including forklift

            complete inventory table


            '''
            if rows:
                for row in rows:
                    oldshelf, oldpallet = row
                    #print("Shelf:", oldshelf)
                    #print("Pallet:", oldpallet)
                    pass
            else:
                print("No matching rows found")

            try:
                cursor.execute(f"UPDATE ItemLocations SET palletUID = %s, timestamp = %s WHERE shelfUID = %s",('Empty',str(currenttime),str(last_uid2)))

                connection.commit()
                print(f"{last_uid1} removed from {last_uid2}")
            except mysql.connector.Error as error:
                print(f'Error:{error} in Pick up Query 1')
            except:
                print("Unknown error in Pick up Query 1")

            try:
                cursor.execute(f"UPDATE ItemLocations SET palletUID = %s,timestamp = %s WHERE shelfUID = %s",(str(last_uid1),str(currenttime),'Forklift 1'))
                connection.commit()
                print(f"{last_uid1} placed on forklift")
            except mysql.connector.Error as error:
                print(f'Error:{error} in Pick up Query 2')
            except:
                print("Unknown error in Pick up Query 2")

            try:
                cursor.execute(f"SELECT shelfUID FROM ItemLocations WHERE shelfUID != 'Forklift 1' AND palletUID = %s",(str(last_uid1),))
                existingLocations = cursor.fetchall()
            except mysql.connector.Error as error:
                print(error)
            except Exception as e:
                print(e)
            if existingLocations:
                existingLocations = existingLocations[0]
                for index in range(len(existingLocations)):
                    loc = existingLocations[index]
                    print(loc)
                    if isinstance(loc,bytearray):
                        loc = loc.decode()
                        loc = str(loc)
                        loc = loc.lstrip("('").rstrip("',)")
                    try:
                        cursor.execute(f"UPDATE ItemLocations SET palletUID = 'Empty' WHERE shelfUID = %s",(str(loc),))
                        cursor.execute(f"UPDATE ErrorStates SET Pallet = %s WHERE Mode = 'Pickup'",(str(last_uid1),))
                        cursor.execute(f"UPDATE ErrorStates SET Location = %s WHERE Mode = 'Pickup'",(str(loc),))
                        connection.commit()
                        print()
                        print(f"{last_uid1} found in other locations, removed from {str(loc)}")
                        print()

                    except mysql.connection.Error as error:
                        print(error)
                    except Exception as e:
                        print(e)


        elif switch == 'D':
            try:
                cursor.execute(f"SELECT shelfUID FROM ItemLocations WHERE palletUID = %s",(str(last_uid1),))
                ShelfReturnArray = cursor.fetchall()

                #print(ShelfReturnArray)
            except mysql.connector.Error as error:
                print(f'Error: {error}')
                ShelfReturn = 'None'
            if ShelfReturnArray:
                for ShelfReturn in ShelfReturnArray:
                    ShelfReturn = ShelfReturn[0]

                    if isinstance(ShelfReturn,bytearray):
                        ShelfReturn = ShelfReturn.decode()
                        ShelfReturn = str(ShelfReturn)
                        ShelfReturn = ShelfReturn.lstrip("('").rstrip("',)")
                        if ShelfReturn != last_uid2 and 'Forklift' not in ShelfReturn:
                            print()
                            print(f"{last_uid1} found in unexpected location {ShelfReturn}")
                            print()
                            cursor.execute(f"UPDATE ErrorStates SET Pallet = %s WHERE Mode = 'Dropoff'",(str(last_uid1),))
                            cursor.execute(f"UPDATE ErrorStates SET Location = %s WHERE Mode = 'Dropoff'",(str(ShelfReturn),))
                            cursor.execute(f"UPDATE ItemLocations SET palletUID = %s WHERE shelfUID = %s",("Empty",str(ShelfReturn)))
                            connection.commit()
                    # delete from all locations
            else:
                #continue
                print("No items in unexpected locations")
            try:
                cursor.execute(f"UPDATE ItemLocations SET palletUID = %s WHERE shelfUID = %s",(str(last_uid1),(str(last_uid2))))
                connection.commit()
                print(f"{last_uid1} placed into {last_uid2}")
            except mysql.connector.Error as error:
                print(f'Error:{error} in Drop off Query 1')
            except:
                print("Unknown error in Drop off Query 1")

            try:
                cursor.execute(f"UPDATE ItemLocations SET palletUID = %s WHERE shelfUID = %s",('Empty','Forklift 1'))
                connection.commit()
                print(f"{last_uid1} removed from forklift")
            except mysql.connector.Error as error:
                print(f'Error:{error} in Drop off Query 2')
            except:
                print("Unknown error in Drop off Query 2")

    if connection.is_connected():
        cursor.close()
        connection.close()



def UpdateSQL(params):
    current_tag = params[0]
    current_uid = params[1]
    current_time = params[2]
    last_pallet_uid = params[3]
    last_pallet_time = params[4]
    last_shelf_uid = params[5]
    last_shelf_time = params[6]
    dropoff_mode = params[7]

    UpdateTable('Pallet', last_pallet_uid,'None','None')
    UpdateTable('Shelf', last_shelf_uid,'None','None')
    try:
        if int(last_pallet_time.split()[2])<= 2 and int(last_shelf_time.split()[2]) <= 2:
            UpdateTable('ItemLocations',last_pallet_uid,last_shelf_uid,dropoff_mode)
            #print(f'{dropoff_mode=}')
    except:("No item scanned / module failed to initiate")


while True:

    if ser_one.in_waiting > 0:
        connection = mysql.connector.connect(host=hostname, database=database, auth_plugin='mysql_native_password', user=username, password=password, port=port)
        cursor = connection.cursor()
        line = ser_one.readline().decode('UTF-8').rstrip()
        if line != "Bad CRC":
            params = decodeSerial(str(line))
            UpdateSQL(params)
        else:
            print("Partial scan, skipping")


    # Close the connection at the end of the script
        if disconnect:
            #connection.commit()
            if connection.is_connected():
                cursor.close()
                connection.close()
            #print("MySQL connection is closed")
    else:
        time.sleep(1) #Wait for one second
        #print("Waiting for RFID Tag")
