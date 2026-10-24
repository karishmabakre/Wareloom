from pymongo import MongoClient

# MongoDB local connection
MONGO_URI = "mongodb://127.0.0.1:27017/"

# Connect to MongoDB
client = MongoClient(MONGO_URI)

# Select database
db = client["wareloom_db"]

# Collections
users_collection = db["users"]
products_collection = db["products"]
suppliers_collection = db["suppliers"]
warehouses_collection = db["warehouses"]
inventory_collection = db["inventory"]
customers_collection = db["customers"]
orders_collection = db["orders"]
shipments_collection = db["shipments"]


# Test connection
try:
    client.admin.command("ping")
    print("MongoDB connected successfully!")
except Exception as e:
    print("MongoDB connection failed:", e)