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
    dim: int = 768,
    enable_overwrite: bool = False
):
    """
    Creates a Milvus collection with the specified schema and GPU-based index.
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
        enable_dynamic_field=True  # Enable dynamic fields for collection
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

    # Step 5: Create a GPU-Based Index
    # Requires specific parameters as per Milvus docs: https://milvus.io/docs/gpu_index.md
    # So, make sure that your instance of Milvus is configured to use GPUs
    # Plus, make sure the necessary GPU resources are available (as defined within your milvus config file, milvus.yaml or whatever)

    index_params = {
        "index_type": "GPU_CAGRA",
        "metric_type": "IP",  # Options: "L2", "IP", "COSINE"
        "params": {
            "intermediate_graph_degree": 21,     # Affects recall and build time by determining the graph’s degree before pruning
            "graph_degree": 16,                  # Sets the graph's degree after pruning. Must be smaller than intermediate_graph_degree
            "build_algo": "NN_DESCENT",          # Chooses the graph generation algorithm (IVF_PQ for higher recall or NN_DESCENT for faster builds with potentially lower recall)
            "itopk_size": 256,                   # Size of intermediate results during the search. Must be at least equal to the final top-K value and typically a power of 2
            "search_width": 8,                   # Number of entry points into the CAGRA graph during the search. Higher values can improve recall but may impact speed
            "min_iterations": 5,                 # Controls the search iteration process. Defaults to 0 (automatic determination)
            "max_iterations": 15,                # Controls the search iteration process. Defaults to 0 (automatic determination)
            "team_size": 16,                     # Number of CUDA threads used for calculating metric distances on the GPU. Defaults to 0 (automatic determination)
            "top-K": 50,                         # Number of returned docs in the search. Higher values can improve recall but may impact speed.
            "cache_dataset_on_device": True      # cache the original dataset in GPU memory (improves recall, but more GPU intensive)
        }
    }

    try:
        existing_indexes = collection.indexes
        # Check if an index already exists on the 'embedding' field
        if any(index.field_name == "embedding" for index in existing_indexes):
            logger.info(f"Index already exists on 'embedding' in collection '{collection_name}'.")
        else:
            # Create the index
            collection.create_index(field_name="embedding", index_params=index_params)
            logger.info(f"GPU_CAGRA index created on 'embedding' with params: {index_params}")
    except Exception as e:
        logger.error(f"An error occurred while creating the index: {e}")
        sys.exit(1)

    # Step 6: Load the Collection into Memory
    try:
        collection.load()
        logger.info(f"Collection '{collection_name}' is loaded into memory.")
    except Exception as e:
        logger.error(f"An error occurred while loading the collection: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_milvus_collection()

