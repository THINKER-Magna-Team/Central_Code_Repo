import pandas as pd
import seaborn as sns
import os  
from time import sleep
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
def init():
    #engine = create_engine('sqlite://', echo=False)
    os.makedirs('MagnaGit/Python_Supermarket', exist_ok=True)  
    global inventory
    inventory = pd.DataFrame
    inventory = pd.read_csv('MagnaGit/Python_Supermarket/out.csv')
def main_loop():
    while 1 == 1:
        print("entry)")
        inventory = pd.read_csv('MagnaGit/Python_Supermarket/out.csv')
        plt.figure(figsize=(12,8))
        plt.bar(inventory['Unnamed: 0'],inventory['Quantity'])
        plt.xlabel("Inventory Locations")
        plt.ylabel("Quantity in Inventory")
        #print("Showing")
        plt.pause(3)
        plt.close()
        #print("Rerunning")
init()
main_loop()