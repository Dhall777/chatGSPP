import argparse
import csv
import json
import logging
import sys
from pymilvus import (
    connections,
    Collection,
    utility,
    DataType
)
from typing import List, Dict, Any


def setup_logging():
    """
    Sets up the logging configuration.
    """
    logger = logging.getLogger("MilvusListAllRecords")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def parse_arguments():
    """
    Parses command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="List 'id', 'file_name', and 'embedding' fields from a Milvus collection."
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
    parser.add_argument(
        "--collection",
        type=str,
        required=True,
        help="Name of the Milvus collection to query."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of records to list. Default is 100. Set to -1 to list all."
    )
    parser.add_argument(
        "--export",
        type=str,
        default=None,
        help="Path to export the records as a CSV file. If not provided, records will be printed to the console."
    )
    parser.add_argument(
        "--truncate",
        action='store_true',
        help="Truncate embeddings in console output for readability."
    )
    parser.add_argument(
        "--display_length",
        type=int,
        default=5,
        help="Number of elements to display from the start and end of the embedding vector when truncating. Default is 5."
    )
    return parser.parse_args()


def truncate_embedding(embedding: List[float], display_length: int = 5) -> str:
    """
    Truncates the embedding vector for concise display.
    
    Args:
        embedding (List[float]): The embedding vector.
        display_length (int): Number of elements to display from the start and end.
    
    Returns:
        str: Truncated embedding string.
    """
    if len(embedding) <= (2 * display_length):
        return str(embedding)
    else:
        start = embedding[:display_length]
        end = embedding[-display_length:]
        return f"{start} ... {end}"


def list_all_records(collection: Collection, limit: int, export_path: str = None, truncate: bool = False, display_length: int = 5):
    """
    Lists the 'id', 'file_name', and 'embedding' fields from the collection.
    
    Args:
        collection (Collection): The Milvus collection to query.
        limit (int): Maximum number of records to list. -1 for all.
        export_path (str, optional): Path to export the records as a CSV file.
        truncate (bool): Whether to truncate embeddings in console output.
        display_length (int): Number of elements to display from the start and end when truncating.
    """
    try:
        if limit == -1:
            # Retrieve all records
            total = collection.num_entities
            logger.info(f"Total number of records in the collection: {total}")
            if total == 0:
                logger.info("The collection is empty.")
                return
            # Query with limit as total
            results = collection.query(
                expr="",
                output_fields=["id", "file_name", "embedding"],
                limit=total
            )
        else:
            # Retrieve up to 'limit' records
            results = collection.query(
                expr="",
                output_fields=["id", "file_name", "embedding"],
                limit=limit
            )
            logger.info(f"Listing up to {limit} records:")
        
        if export_path:
            export_to_csv(results, export_path)
            logger.info(f"Successfully exported records to {export_path}")
        else:
            # Print records to console
            for idx, record in enumerate(results, start=1):
                record_id = record.get("id", "")
                file_name = record.get("file_name", "")
                embedding = record.get("embedding", [])
                
                if truncate:
                    embedding_display = truncate_embedding(embedding, display_length)
                else:
                    embedding_display = embedding
                
                logger.info(f"Record {idx}:")
                logger.info(f"  ID: {record_id}")
                logger.info(f"  File Name: {file_name}")
                logger.info(f"  Embedding: {embedding_display}\n")
    
    except Exception as e:
        logger.error(f"Failed to list records: {e}")
        sys.exit(1)


def export_to_csv(records: List[Dict[str, Any]], output_file: str):
    """
    Exports the records to a CSV file.
    
    Args:
        records (List[Dict[str, Any]]): List of records retrieved from Milvus.
        output_file (str): Path to the output CSV file.
    """
    try:
        with open(output_file, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # Write header
            writer.writerow(["Record_Number", "ID", "File_Name", "Embedding"])
            for idx, record in enumerate(records, start=1):
                record_id = record.get("id", "")
                file_name = record.get("file_name", "")
                embedding = record.get("embedding", [])
                # Convert embedding list to a JSON string for CSV
                embedding_str = json.dumps(embedding)
                writer.writerow([idx, record_id, file_name, embedding_str])
    except Exception as e:
        logger.error(f"Failed to export records to CSV: {e}")
        sys.exit(1)


def main():
    global logger
    logger = setup_logging()
    args = parse_arguments()
    
    # Connect to Milvus
    try:
        connections.connect(host=args.host, port=args.port)
        logger.info(f"Connected to Milvus at {args.host}:{args.port}")
    except Exception as e:
        logger.error(f"Failed to connect to Milvus: {e}")
        sys.exit(1)
    
    # Check if collection exists
    if not utility.has_collection(args.collection):
        logger.error(f"Collection '{args.collection}' does not exist.")
        sys.exit(1)
    
    collection = Collection(name=args.collection)
    logger.info(f"Loaded collection '{args.collection}'.")
    
    # List 'id', 'file_name', and 'embedding' fields
    list_all_records(
        collection=collection,
        limit=args.limit,
        export_path=args.export,
        truncate=args.truncate,
        display_length=args.display_length
    )


if __name__ == "__main__":
    main()
