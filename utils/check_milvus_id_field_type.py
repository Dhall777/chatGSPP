from pymilvus import connections, Collection, utility

def check_id_field_type(collection_name, host='localhost', port='19530'):
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

        # Step 4: Retrieve schema
        schema = collection.schema
        id_field = None
        for field in schema.fields:
            if field.name == "id":
                id_field = field
                break

        if id_field:
            print(f"Field 'id' found with the following properties:")
            print(f" - Type: {id_field.dtype.name}")
            print(f" - Parameters: {id_field.params}")
            print(f" - Is Primary: {id_field.is_primary}")
            print(f" - Auto ID: {id_field.auto_id}\n")
        else:
            print("Field 'id' does not exist in the schema.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    check_id_field_type("milvus_db")

