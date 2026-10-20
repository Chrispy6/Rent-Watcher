from fastapi import FastAPI
import json
from pathlib import Path


# create our backend
app = FastAPI()


#allows us to check if our backend is running properly 
@app.get("/alive")

def health():
    return {"status": "ok", "application": "Rent Watcher"}



#lets us check if our listings are loaded into our backend
@app.get("/listings")

def get_listings():
    #grabs our Rent-Watcher folder
    project_folder = Path(__file__).resolve().parent.parent

    #grab our listings folder
    listings_file = project_folder/"Golden_Listings.json"

    #read our json listings and convert them into python data
    with listings_file.open("r", encoding="utf-8") as file:
        listings = json.load(file)

    return listings