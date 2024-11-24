from pymilvus import connections, Collection, utility
import json
import sys
import logging

def setup_logging():
    """
    Sets up the logging configuration.
    """
    logger = logging.getLogger("InspectMetaFields")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def inspect_meta_fields(
    host: str = 'localhost',
    port: str = '19530',
    collection_name: str = 'chatgspp',
    limit: int = 10
):
    """
    Retrieves and prints the contents of the $meta field from the specified collection.

    Args:
        host (str): Milvus server host.
        port (str): Milvus server port.
        collection_name (str): Name of the collection to inspect.
        limit (int): Number of records to retrieve.
    """
    logger = setup_logging()

    # Step 1: Connect to Milvus
    try:
        connections.connect(host=host, port=port)
        logger.info(f"Connected to Milvus at {host}:{port}")
    except Exception as e:
        logger.error(f"Failed to connect to Milvus: {e}")
        sys.exit(1)

    # Step 2: Check if Collection Exists
    try:
        if not utility.has_collection(collection_name):
            logger.error(f"Collection '{collection_name}' does not exist.")
            sys.exit(1)
        collection = Collection(name=collection_name)
        logger.info(f"Loaded collection '{collection_name}'.")
    except Exception as e:
        logger.error(f"Error loading collection: {e}")
        sys.exit(1)

    # Step 3: Check if $meta Field Exists
    try:
        meta_field_exists = any(field.name == "$meta" for field in collection.schema.fields)
        if not meta_field_exists:
            logger.info(f"No dynamic fields found in collection '{collection_name}'.")
            sys.exit(0)
        logger.info("Dynamic fields are enabled. Inspecting the $meta field.")
    except Exception as e:
        logger.error(f"Error checking for $meta field: {e}")
        sys.exit(1)

    # Step 4: Query the $meta Field
    try:
        results = collection.query(
            expr="",
            output_fields=["id", "$meta"],
            limit=limit
        )

        if not results:
            logger.info("No records found in the collection.")
            sys.exit(0)

        for idx, res in enumerate(results, start=1):
            logger.info(f"\nRecord {idx}:")
            logger.info(f"  ID: {res['id']}")
            meta = res.get('$meta', '{}')
            try:
                meta_json = json.loads(meta)
                logger.info(f"  Metadata Fields: {json.dumps(meta_json, indent=4)}")
            except json.JSONDecodeError:
                logger.warning(f"  Unable to parse $meta field: {meta}")
    except Exception as e:
        logger.error(f"An error occurred while querying the $meta field: {e}")
        sys.exit(1)

if __name__ == "__main__":
    inspect_meta_fields()
