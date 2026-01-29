from pymongo import MongoClient


def copy_mongodb(source_uri, source_db_name, target_uri, target_db_name):
    source_client = MongoClient(source_uri)
    target_client = MongoClient(target_uri)

    source_db = source_client[source_db_name]
    target_db = target_client[target_db_name]

    collections = source_db.list_collection_names()
    for coll_name in collections:
        source_coll = source_db[coll_name]
        target_coll = target_db[coll_name]

        docs = list(source_coll.find({}))
        if docs:
            target_coll.delete_many({})
            target_coll.insert_many(docs)
            print(f"Copied {len(docs)} documents in collection '{coll_name}'")
        else:
            print(f"Collection '{coll_name}' is empty, skipped.")

    print('✅ All collections copied.')

if __name__ == '__main__':
    # Example usage:
    # python copy_mongo.py
    source_uri = 'mongodb+srv://analytics_user:v5AY68O9ibnROSeA@rusl-dev.gt04nun.mongodb.net'
    source_db_name = 'biom'
    target_uri = 'mongodb://localhost:27017'
    target_db_name = 'biom'
    copy_mongodb(source_uri, source_db_name, target_uri, target_db_name)
