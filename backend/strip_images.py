from db import halls_collection
halls_collection.update_many({}, {"$unset": {"image": ""}})
print("Images removed from existing MongoDB halls!")
