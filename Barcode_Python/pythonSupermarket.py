#from sqlalchemy import create_engine
import pandas as pd
#import seaborn as sns
import os  
def init():
    #engine = create_engine('sqlite://', echo=False)
    os.makedirs('MagnaGit/Python_Supermarket', exist_ok=True)  
    global inventory 
    data_init={'Quantity':[0,0,0,0,0,0,0,0]}
    inventory = pd.DataFrame(data=data_init)
    inventory=inventory.set_axis(['01-01-01-01','01-01-01-02','01-01-01-03','01-01-01-04','01-01-02-01','01-01-02-02','01-01-02-03','01-01-02-04'], axis='index')
    #display(inventory)
def main_loop():
    while 1 == 1:
        print("Pickup or Dropoff> Type P for Pickup,Type D for Dropoff")
        action=input().lower()
        #print(action)
        print("Enter Quantity of Boxes")
        quantity = input()
        #print(quantity)p
        print("Scan the Location Tag:")
        location = input().lstrip("^[^[")
        #print(location)
        enter_inventory(action,location,quantity)
def enter_inventory(action,loc,quant):
    quant=int(quant)
    match action:
        case "d":
            inventory.loc[loc]=inventory.loc[loc]+quant
        case "p":
            inventory.loc[loc]=inventory.loc[loc]-quant
    inventory.to_csv('MagnaGit/Python_Supermarket/out.csv', index=True)

init()
main_loop()