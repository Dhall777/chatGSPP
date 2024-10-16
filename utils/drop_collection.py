from pymilvus import connections, Collection, utility

def list_milvus_collections(host='localhost', port='19530'):
    # Step 1: Connect to Milvus
    connections.connect(alias="default", host=host, port=port)

    # Step 3: Delete all collections
    utility.drop_collection("milvus_db")
