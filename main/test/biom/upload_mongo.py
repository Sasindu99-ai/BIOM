import os

from bson import json_util
from pymongo import MongoClient

# === CONFIGURATION ===
CONNECTION_STRING = 'mongodb+srv://sasindu:AkLbqqTXasLNCsGc@cluster0.a2agenc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'  # Local MongoDB (change if needed)
DATABASE_NAME = 'biom'      # Target DB name
INPUT_DIR = 'collections'                       # Folder with JSON files


def restore_mongodb(connection_string, db_name, input_dir):
    client = MongoClient(connection_string)
    db = client[db_name]

    # Ensure input_dir exists
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        print(f"📁 Created input folder '{input_dir}'. Please add collection folders or .json files and rerun.")
        return

    # Find all .json files in input_dir and its subfolders
    json_files = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))

    if not json_files:
        print(f"❌ No .json files found in '{input_dir}' or its subfolders.")
        return

    for file_path in json_files:
        # Determine collection name: either parent folder or file name (without .json)
        rel_path = os.path.relpath(file_path, input_dir)
        parts = rel_path.split(os.sep)
        if len(parts) > 1:
            coll_name = parts[0]
        else:
            coll_name = parts[0].replace('.json', '')

        # If you ever need to write files, ensure the collection folder exists:
        # coll_folder = os.path.join(input_dir, coll_name)
        # if not os.path.exists(coll_folder):
        #     os.makedirs(coll_folder)

        with open(file_path, encoding='utf-8') as f:
            data = json_util.loads(f.read())

        if data:
            collection = db[coll_name]
            collection.delete_many({})
            result = collection.insert_many(data)
            print(f"✅ Restored {len(result.inserted_ids)} documents to '{coll_name}' from '{file_path}'")
        else:
            print(f"⚠️ Skipped '{coll_name}' (file '{file_path}' empty)")

    print('🎉 Restore completed!')


if __name__ == '__main__':
    restore_mongodb(CONNECTION_STRING, DATABASE_NAME, INPUT_DIR)
