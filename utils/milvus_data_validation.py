from pymilvus import connections, Collection, utility

def verify_data_consistency(collection_name, host='localhost', port='19530', sample_id='doc1.csv'):
    try:
        # Connect to Milvus
        connections.connect(alias="default", host=host, port=port)
        print(f"Connected to Milvus at {host}:{port}.\n")

        # Check if collection exists
        if not utility.has_collection(collection_name):
            print(f"Collection '{collection_name}' does not exist.")
            return

        # Load the collection
        collection = Collection(collection_name)
        collection.load()
        print(f"Collection '{collection_name}' loaded successfully.\n")

        # Count entities
        num_entities = collection.num_entities
        print(f"Number of entities in Collection '{collection_name}': {num_entities}\n")

        # Perform a broad query
        print("Performing a broad query to retrieve all 'id' fields.")
        all_ids = collection.query(expr="id != ''", output_fields=["id"], limit=num_entities)
        retrieved_ids = [doc['id'] for doc in all_ids]
        print(f"Retrieved {len(retrieved_ids)} 'id' fields.\n")

        # Check if specific sample_id exists
        if sample_id in retrieved_ids:
            print(f"Sample ID '{sample_id}' exists in the collection.\n")
        else:
            print(f"Sample ID '{sample_id}' does NOT exist in the collection.\n")

        # Optionally, retrieve embedding for the sample_id
        if sample_id in retrieved_ids:
            expr = f"id == '{sample_id}'"
            results = collection.query(expr=expr, output_fields=["embedding"], limit=1)
            if results:
                print(f"Embedding for '{sample_id}': {results[0]['embedding']}\n")
            else:
                print(f"Failed to retrieve embedding for '{sample_id}'.\n")
        else:
            print(f"Cannot retrieve embedding as '{sample_id}' does not exist.\n")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Replace 'doc1.csv' with an actual ID present in your collection
    verify_data_consistency("milvus_db", sample_id="doc1.csv")

