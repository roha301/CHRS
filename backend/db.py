from pymongo import MongoClient
import os
from dotenv import load_dotenv
from data import halls as seed_halls

load_dotenv()

# Initialize MongoDB client
uri = os.getenv('MONGODB_URI')
client = MongoClient(uri)
db = client.get_database('chrs') # Default DB name

# Collections
users_collection = db.users
halls_collection = db.halls
bookings_collection = db.bookings
events_collection = db.events
notifications_collection = db.notifications
# Each document in 'participants' sub-collection can be denormalized into events_collection

def init_db():
    # Insert default halls if empty
    if halls_collection.count_documents({}) == 0:
        halls_collection.insert_many(seed_halls)
        print("Inserted default halls into MongoDB.")

