import argparse
from pymilvus import connections, utility, Collection
import sys
import logging

def setup_logging():
    """
    Sets up the logging configuration.
    """
    logger = logging.getLogger("DropMilvusCollection")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def list_collections(logger):
    """
    Lists all existing collections in Milvus.
    """
    try:
        collections = utility.list_collections()
        if collections:
            logger.info("Existing Collections:")
            for idx, name in enumerate(collections, start=1):
                logger.info(f"  {idx}. {name}")
        else:
            logger.info("No collections found in Milvus.")
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        sys.exit(1)

def drop_collection(collection_name: str, host: str, port: str, logger):
    """
    Drops the specified Milvus collection after confirmation.
    
    Args:
        collection_name (str): Name of the collection to drop.
        host (str): Milvus server host.
        port (str): Milvus server port.
        logger (logging.Logger): Logger instance.
    """
    # Step 1: Connect to Milvus
    try:
        connections.connect(host=host, port=port)
        logger.info(f"Connected to Milvus at {host}:{port}")
    except Exception as e:
        logger.error(f"Failed to connect to Milvus: {e}")
        sys.exit(1)
    
    # Step 2: Check if Collection Exists
    try:
        if utility.has_collection(collection_name):
            logger.info(f"Collection '{collection_name}' exists.")
        else:
            logger.warning(f"Collection '{collection_name}' does not exist.")
            sys.exit(0)
    except Exception as e:
        logger.error(f"Error checking collection existence: {e}")
        sys.exit(1)
    
    # Optional: List all collections before deletion
    logger.info("Current Collections in Milvus:")
    list_collections(logger)
    
    # Step 3: Confirm Deletion
    confirmation = input(f"\nAre you sure you want to drop the collection '{collection_name}'? This action cannot be undone. (yes/no): ").strip().lower()
    if confirmation not in ['yes', 'y']:
        logger.info("Collection drop aborted by the user.")
        sys.exit(0)
    
    # Step 4: Drop the Collection
    try:
        collection = Collection(name=collection_name)
        collection.drop()
        logger.info(f"Collection '{collection_name}' has been successfully dropped.")
    except Exception as e:
        logger.error(f"Failed to drop collection '{collection_name}': {e}")
        sys.exit(1)
    
    # Optional: List collections after deletion
    logger.info("\nCollections after deletion:")
    list_collections(logger)

def main():
    # Setup logging
    logger = setup_logging()
    
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Drop a Milvus collection.")
    parser.add_argument(
        "-c", "--collection",
        type=str,
        required=True,
        help="Name of the Milvus collection to drop."
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Milvus server host. Default is 'localhost'."
    )
    parser.add_argument(
        "--port",
        type=str,
        default="19530",
        help="Milvus server port. Default is '19530'."
    )
    
    args = parser.parse_args()
    
    # Execute drop_collection function
    drop_collection(
        collection_name=args.collection,
        host=args.host,
        port=args.port,
        logger=logger
    )

if __name__ == "__main__":
    main()

