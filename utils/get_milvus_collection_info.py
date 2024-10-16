from pymilvus import connections, Collection, utility

def get_collection_info(collection_name, host='localhost', port='19530'):
    # Step 1: Connect to Milvus
    connections.connect(alias="default", host=host, port=port)

    # Step 2: Check if collection exists
    if not utility.has_collection(collection_name):
        print(f"Collection '{collection_name}' does not exist in Milvus DB.")
        return

    # Step 3: Load the collection
    collection = Collection(collection_name)

    # Step 4: Retrieve and print schema
    schema = collection.schema
    print(f"Schema for Collection '{collection_name}':")
    for field in schema.fields:
        print(f" - Field Name: {field.name}")
        print(f"   Description: {field.description}")
        print(f"   Type: {field.dtype.name}")  # Use 'name' for readable type
        print(f"   Parameters: {field.params}")
        print(f"   Is Primary: {field.is_primary}")
        print(f"   Auto ID: {field.auto_id}")
        print()

    # Step 5: Retrieve and print statistics using utility.get_collection_stats
    try:
        #stats = utility.get_collection_stats(collection_name)
        stats = client.describe_collection(collection_name="collection_name")
        print(f"Statistics for Collection '{collection_name}':")
        print(stats)
    except Exception as e:
        print(f"An error occurred while retrieving statistics: {e}")

if __name__ == "__main__":
    # Replace 'milvus_db' with your actual collection name
    get_collection_info("milvus_db")
