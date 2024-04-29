import pymsteams
import pandas as pd
import os
import serial as ser
import time
#Functions
def init():
    #engine = create_engine('sqlite://', echo=False)
    os.makedirs('MagnaGit/Python_Supermarket', exist_ok=True)
    global inventory
    data_init={'Quantity':[0,0,0,0,0,0,0,0]}
    inventory = pd.DataFrame(data=data_init)
    inventory=inventory.set_axis(['01-01-01-01','01-01-01-02','01-01-01-03','01-01-01-04','01-01-02-01','01-01-02-02','01-01-02-03','01-01-02-04'], axis='index')
    #display(inventory)
def enter_inventory(action,loc,quant):
    quant=int(quant)
    match action:
        case "d":
            inventory.loc[loc]=inventory.loc[loc]+quant
        case "p":
            inventory.loc[loc]=inventory.loc[loc]-quant
        case "inv":
            inventory.loc[loc]=quant
    inventory.to_csv('MagnaGit/Python_Supermarket/out.csv', index=True)

operator_level = pymsteams.connectorcard("https://clemson.webhook.office.com/webhookb2/82391c2f-e78c-4900-baa1-ec63edf23ec8@0c9bf8f6-ccad-4b87-818d-49026938aa97/IncomingWebhook/a9693c094cf940e3aa622bf34f51822b/e3fc42f8-a678-4b01-ac80-f8c8eb6df764")
#operator_level = pymsteams.connectorcard("https://clemson.webhook.office.com/webhookb2/82391c2f-e78c-4900-baa1-ec63edf23ec8@0c9bf8f6-ccad-4b87-818d-49026938aa97/IncomingWebhook/3d0f86252c824c49b202287cb17b76c8/e3fc42f8-a678-4b01-ac80-f8c8eb6df764") #Testing Server
supervisor_level = pymsteams.connectorcard("https://clemson.webhook.office.com/webhookb2/82391c2f-e78c-4900-baa1-ec63edf23ec8@0c9bf8f6-ccad-4b87-818d-49026938aa97/IncomingWebhook/da6556a6dc224494931b29580df7c1e8/e3fc42f8-a678-4b01-ac80-f8c8eb6df764")
#supervisor_level = pymsteams.connectorcard("https://clemson.webhook.office.com/webhookb2/82391c2f-e78c-4900-baa1-ec63edf23ec8@0c9bf8f6-ccad-4b87-818d-49026938aa97/IncomingWebhook/3d0f86252c824c49b202287cb17b76c8/e3fc42f8-a678-4b01-ac80-f8c8eb6df764")
# Serial Communication Parameters
USB_PORT_ONE = "/dev/cu.usbserial-0001" #Serial Port for Arduino 1-Need to run 'ls /dev/tty.* to find connected arduinos
BAUD_RATE = 115200
low_inv_count = 0
urgent_message_sent=False
ser_one = ser.Serial(USB_PORT_ONE ,BAUD_RATE, timeout=1)
ser_one.reset_input_buffer() #Resets input buffer to prevent lingering signals
init()
while True:
    if ser_one.in_waiting > 0:
        try:
            line = ser_one.readline().decode('UTF-8').rstrip()
            ser_one.reset_input_buffer() #Resets input buffer to prevent lingering signals
        except UnicodeDecodeError:
            continue
        shelf_inventory = line.split(",")
        enter_inventory("inv","01-01-02-01",int(shelf_inventory[0]))
        enter_inventory("inv","01-01-02-02",int(shelf_inventory[1]))
        if int(shelf_inventory[2])!=1:
            low_inv_count +=1
            print(low_inv_count)
            if low_inv_count%10==0:
                operator_level.text("Insufficient Inventory in location 01-01-02-03")
                operator_level.send()
            if not urgent_message_sent and low_inv_count>180:
                supervisor_level.text("URGENT. Location 01-01-02-03 has had insufficient inventory for over 3 minutes.")
                supervisor_level.send()
                urgent_message_sent=True
            else:
                continue
        else:
            low_inv_count = 0
            urgent_message_sent=False
