from pymilvus import connections, Collection, utility

def comprehensive_query_using_id(collection_name, host='localhost', port='19530', limit=10):
    try:
        # Step 1: Connect to Milvus
        connections.connect(alias="default", host=host, port=port)
        print(f"Connected to Milvus at {host}:{port}.")

        # Step 2: Check if collection exists
        if not utility.has_collection(collection_name):
            print(f"Collection '{collection_name}' does not exist.")
            return

        # Step 3: Load the collection
        collection = Collection(collection_name)
        collection.load()
        print(f"Collection '{collection_name}' loaded successfully.")

        # Step 4: Inspect schema
        schema = collection.schema
        field_names = [field.name for field in schema.fields]
        print("\nCollection Schema:")
        for field in schema.fields:
            print(f" - {field.name} ({field.dtype.name})")
        print(f"\nFields available for querying: {field_names}")

        # Step 5: Perform the query using 'id' field
        expr = "id != ''"
        print(f"\nExecuting query: {expr} with limit={limit}")
        results = collection.query(
            expr=expr,
            output_fields=["id", "embedding"],
            limit=limit
        )

        # Step 6: Display results
        if results:
            print(f"\nRetrieved {len(results)} documents:")
            for idx, doc in enumerate(results, start=1):
                file_name = doc.get("id", "Unknown File")
                embedding = doc.get("embedding", [])
                print(f"Record {idx}:")
                print(f" - **Source File:** {file_name}")
                print(f" - **Embedding Vector:** {embedding}\n")
        else:
            print("No documents found matching the query.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    comprehensive_query_using_id("milvus_db", limit=10)
