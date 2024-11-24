from pymilvus import connections, utility

def list_milvus_collections(host='localhost', port='19530'):
    # Step 1: Connect to Milvus
    connections.connect(alias="default", host=host, port=port)

    # Step 2: List all collections
    collections = utility.list_collections()

    # Step 3: Display the collections
    if collections:
        print("Collections in Milvus DB:")
        for idx, collection in enumerate(collections, start=1):
            print(f"{idx}. {collection}")
    else:
        print("No collections found in Milvus DB.")

if __name__ == "__main__":
    list_milvus_collections()
