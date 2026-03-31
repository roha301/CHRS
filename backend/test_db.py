from db import db, client, halls_collection, users_collection
print(halls_collection.count_documents({}))
print(users_collection.count_documents({}))
print("MongoDB is working!")
