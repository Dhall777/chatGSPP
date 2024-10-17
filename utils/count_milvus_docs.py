from pymilvus import connections, Collection, utility

def count_entities(collection_name, host='localhost', port='19530'):
    try:
        # Step 1: Connect to Milvus
        connections.connect(alias="default", host=host, port=port)
        print(f"Connected to Milvus at {host}:{port}.\n")

        # Step 2: Check if the collection exists
        if not utility.has_collection(collection_name):
            print(f"Collection '{collection_name}' does not exist.")
            return

        # Step 3: Load the collection
        collection = Collection(collection_name)
        collection.load()
        print(f"Collection '{collection_name}' loaded successfully.\n")

        # Step 4: Get number of entities
        num_entities = collection.num_entities
        print(f"Number of entities in Collection '{collection_name}': {num_entities}\n")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    count_entities("milvus_db")

