from pymilvus import connections, Collection, utility

def comprehensive_query(collection_name, host='localhost', port='19530', limit=10):
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

        if num_entities == 0:
            print("No entities found in the collection.")
            return

        # Step 5: Perform a broad query
        print(f"Executing broad query to retrieve first {limit} documents:")
        results = collection.query(expr="id != ''", output_fields=["id", "embedding"], limit=limit)

        if results:
            for idx, doc in enumerate(results, start=1):
                file_name = doc.get("id", "Unknown File")
                embedding = doc.get("embedding", [])
                print(f"Record {idx}:")
                print(f" - **Source File:** {file_name}")
                print(f" - **Embedding Vector:** {embedding}\n")
        else:
            print("No documents found matching the query.")
    except Exception as e:
        print(f"An error occurred during querying: {e}")

if __name__ == "__main__":
    comprehensive_query("milvus_db", limit=10)

