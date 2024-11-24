from pymilvus import connections, Collection, utility

def inspect_collection_schema(collection_name, host='localhost', port='19530'):
    # Step 1: Connect to Milvus
    connections.connect(alias="default", host=host, port=port)

    # Step 2: Check if the collection exists
    if not utility.has_collection(collection_name):
        print(f"Collection '{collection_name}' does not exist.")
        return

    # Step 3: Load the collection
    collection = Collection(collection_name)
    collection.load()

    # Step 4: Retrieve and print schema
    schema = collection.schema
    print(f"Schema for Collection '{collection_name}':")
    for field in schema.fields:
        print(f" - Field Name: {field.name}")
        print(f"   Description: {field.description}")
        print(f"   Type: {field.dtype.name}")
        print(f"   Parameters: {field.params}")
        print(f"   Is Primary: {field.is_primary}")
        print(f"   Auto ID: {field.auto_id}")
        print()

    # Step 5: Check if 'file_name' field exists
    field_names = [field.name for field in schema.fields]
    if "file_name" in field_names:
        print("'file_name' field exists in the schema.")
    else:
        print("'file_name' field does NOT exist in the schema.")

if __name__ == "__main__":
    inspect_collection_schema("chatgspp")
