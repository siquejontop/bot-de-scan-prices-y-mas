from pymongo import MongoClient
import os

mongo_uri = os.getenv("MONGO_URI")

try:
    client = MongoClient(mongo_uri)
    db = client["siquej"]  # Nombre de tu base de datos
    client.admin.command('ping')
    print("✅ Conectado exitosamente a MongoDB Atlas.")
except Exception as e:
    print("❌ Error al conectar con MongoDB:", e)
