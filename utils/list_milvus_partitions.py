from pymilvus import connections, Collection, utility

def list_partitions(collection_name, host='localhost', port='19530'):
    try:
        # Step 1: Connect to Milvus
        connections.connect(alias="default", host=host, port=port)
        print(f"Connected to Milvus at {host}:{port}.\n")

        # Step 2: Check if collection exists
        if not utility.has_collection(collection_name):
            print(f"Collection '{collection_name}' does not exist.")
            return

        # Step 3: Load the collection
        collection = Collection(collection_name)
        collection.load()
        print(f"Collection '{collection_name}' loaded successfully.\n")

        # Step 4: List partitions
        partitions = collection.partitions
        if partitions:
            print(f"Partitions in Collection '{collection_name}':")
            for partition in partitions:
                print(f" - {partition.name}")
        else:
            print(f"No partitions found in Collection '{collection_name}'.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    list_partitions("milvus_db")

