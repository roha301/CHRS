"""One-time script to clear all CHRS collections in MongoDB."""
from db import users_collection, halls_collection, bookings_collection, events_collection

print("Clearing all collections...")
users_collection.delete_many({})
halls_collection.delete_many({})
bookings_collection.delete_many({})
events_collection.delete_many({})
print("All collections cleared successfully.")
print("Default halls will be re-seeded on next server start.")
