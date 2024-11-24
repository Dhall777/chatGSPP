from pymilvus import (
    connections,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    utility
)
import sys
import logging

def setup_logging():
    """
    Sets up the logging configuration.
    """
    logger = logging.getLogger("CreateMilvusCollection")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def create_milvus_collection(
    host: str = 'localhost',
    port: str = '19530',
    collection_name: str = 'chatgspp',
    dim: int = 384,
    enable_overwrite: bool = False
):
    """
    Creates a Milvus collection with the specified schema and index.
    Enables dynamic fields to allow insertion of unexpected fields.

    Args:
        host (str): Milvus server host.
        port (str): Milvus server port.
        collection_name (str): Name of the collection to create.
        dim (int): Dimension of the embedding.
        enable_overwrite (bool): If True, drops the existing collection before creation.
    """
    logger = setup_logging()

    # Step 1: Connect to Milvus
    try:
        connections.connect(host=host, port=port)
        logger.info(f"Connected to Milvus at {host}:{port}")
    except Exception as e:
        logger.error(f"Failed to connect to Milvus: {e}")
        sys.exit(1)

    # Step 2: Define the Fields
    id_field = FieldSchema(
        name="id",
        dtype=DataType.VARCHAR,
        max_length=65535,
        is_primary=True,
        auto_id=False
    )

    file_name_field = FieldSchema(
        name="file_name",
        dtype=DataType.VARCHAR,
        max_length=65535,
        is_primary=False,
        auto_id=False
    )

    embedding_field = FieldSchema(
        name="embedding",
        dtype=DataType.FLOAT_VECTOR,
        dim=dim,
        is_primary=False,
        auto_id=False
    )

    # Step 3: Create the Collection Schema with Dynamic Fields Enabled
    schema = CollectionSchema(
        fields=[id_field, file_name_field, embedding_field],
        description="Collection of documents with file names and embedding.",
        enable_dynamic_field=True  # Enable/disable dynamic fields for collection
    )

    # Step 4: Handle Existing Collection
    try:
        if utility.has_collection(collection_name):
            logger.info(f"Collection '{collection_name}' already exists.")
            if enable_overwrite:
                logger.info(f"Dropping existing collection '{collection_name}' as overwrite is enabled.")
                collection = Collection(name=collection_name)
                collection.drop()
                logger.info(f"Collection '{collection_name}' dropped successfully.")
                collection = Collection(name=collection_name, schema=schema)
                logger.info(f"Collection '{collection_name}' created successfully with new schema.")
            else:
                logger.info(f"Using existing collection '{collection_name}'.")
                collection = Collection(name=collection_name)
        else:
            collection = Collection(name=collection_name, schema=schema)
            logger.info(f"Collection '{collection_name}' created successfully.")
    except Exception as e:
        logger.error(f"An error occurred while handling the collection: {e}")
        sys.exit(1)

    # Step 5: Create an Index (for the db's nearest neightbor search engine)
    index_params = {
        "index_type": "HNSW",
        "metric_type": "IP",  # Options: "L2", "IP", "COSINE"
        "params": {
            "M": 32,               # M defines tha maximum number of outgoing connections in the graph. Higher M leads to higher accuracy/run_time at fixed ef/efConstruction
            "efConstruction": 10,  # ef_construction controls index search speed/build speed tradeoff. Increasing the efConstruction parameter may enhance index quality, but it also tends to lengthen the indexing time
            "ef": 5                # Parameter controlling query time/accuracy trade-off. Higher ef leads to more accurate but slower search (min = top-k)
        }
    }

    try:
        existing_indexes = collection.indexes
        if "embedding" in existing_indexes:
            logger.info(f"Index already exists on 'embedding' in collection '{collection_name}'.")
        else:
            collection.create_index(field_name="embedding", index_params=index_params)
            logger.info(f"Index created on 'embedding' with params: {index_params}")
    except Exception as e:
        logger.error(f"An error occurred while creating the index: {e}")
        sys.exit(1)

    # Step 6: Load the Collection into Memory (Optional)
    try:
        collection.load()
        logger.info(f"Collection '{collection_name}' is loaded into memory.")
    except Exception as e:
        logger.error(f"An error occurred while loading the collection: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_milvus_collection()
