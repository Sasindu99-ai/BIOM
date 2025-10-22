import json
import os
from pymongo import MongoClient
from bson import json_util

# === CONFIGURATION ===
CONNECTION_STRING = "mongodb+srv://analytics_user:v5AY68O9ibnROSeA@rusl-dev.gt04nun.mongodb.net"  # Replace with your MongoDB connection string
DATABASE_NAME = "biom"  # Replace with your database name
OUTPUT_DIR = "biom"  # Folder to save JSON files

def export_mongodb(connection_string, db_name, output_dir):
    client = MongoClient(connection_string)
    db = client[db_name]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    collections = db.list_collection_names()
    print(f"Found collections: {collections}")

    for coll_name in collections:
        collection = db[coll_name]
        data = list(collection.find({}))

        file_path = os.path.join(output_dir, f"{coll_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            # Use bson.json_util to serialize MongoDB-specific types
            f.write(json_util.dumps(data, indent=4, ensure_ascii=False))

        print(f"✅ Exported {len(data)} documents from '{coll_name}' to {file_path}")

    print("🎉 Export completed!")


if __name__ == "__main__":
    export_mongodb(CONNECTION_STRING, DATABASE_NAME, OUTPUT_DIR)