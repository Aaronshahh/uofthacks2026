#!/usr/bin/env python3
"""
Standalone data ingestion script for the Footwear RAG Agent.

Usage:
    python ingest_data.py [--zip-dir PATH] [--csv PATH] [--drop-existing]

This script:
1. Extracts images from zip files
2. Parses CSV metadata
3. Matches images to metadata by ID
4. Generates embeddings
5. Stores data in Snowflake vector database
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from footwear_rag.backend.config import get_config, load_config
from footwear_rag.backend.data_processor import DataProcessor
from footwear_rag.backend.database import SnowflakeVectorDB
from footwear_rag.backend.embeddings import EmbeddingService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ingestion.log")
    ]
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Ingest footprint data into Snowflake vector database"
    )
    parser.add_argument(
        "--zip-dir",
        type=str,
        help="Path to directory containing zip files (uses config default if not provided)"
    )
    parser.add_argument(
        "--csv",
        type=str,
        help="Path to metadata CSV file (uses config default if not provided)"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (uses default config/config.yaml if not provided)"
    )
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop existing table before ingestion"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for database insertion (default: 100)"
    )
    parser.add_argument(
        "--use-local-embeddings",
        action="store_true",
        help="Use local embedding generation instead of Snowflake Cortex"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process data without inserting into database"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main():
    """Main ingestion function."""
    args = parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("=" * 60)
    logger.info("Footwear RAG Agent - Data Ingestion")
    logger.info("=" * 60)
    
    start_time = datetime.now()
    
    # Load configuration
    try:
        if args.config:
            config = load_config(args.config)
        else:
            config = get_config()
        logger.info("Configuration loaded successfully")
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        logger.error("Please create config/config.yaml with your Snowflake credentials")
        sys.exit(1)
    
    # Initialize services
    try:
        processor = DataProcessor()
        logger.info("Data processor initialized")
        
        if not args.dry_run:
            db = SnowflakeVectorDB()
            logger.info("Connected to Snowflake")
            
            # Create table
            db.create_table(drop_existing=args.drop_existing)
            if args.drop_existing:
                logger.info("Dropped and recreated table")
        
        embedding_service = EmbeddingService()
        use_snowflake = not args.use_local_embeddings
        logger.info(f"Embedding service initialized (Snowflake: {use_snowflake})")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        sys.exit(1)
    
    # Process data
    zip_dir = args.zip_dir
    csv_path = args.csv
    
    logger.info(f"Zip directory: {zip_dir or config.data.zip_directory}")
    logger.info(f"CSV file: {csv_path or config.data.csv_file}")
    
    records_processed = 0
    records_failed = 0
    records_to_insert = []
    
    try:
        for record in processor.process_all(zip_directory=zip_dir, csv_path=csv_path):
            try:
                # Validate image
                if not processor.validate_image(record.image_data):
                    logger.warning(f"Invalid image for ID {record.id}, skipping")
                    records_failed += 1
                    continue
                
                # Generate embedding
                embedding = embedding_service.generate_embedding(
                    record.image_data,
                    use_snowflake=use_snowflake
                )
                
                records_to_insert.append({
                    "id": record.id,
                    "image_path": record.image_path,
                    "metadata": record.metadata,
                    "embedding": embedding
                })
                
                records_processed += 1
                
                if records_processed % 10 == 0:
                    logger.info(f"Processed {records_processed} records...")
                
                # Batch insert
                if len(records_to_insert) >= args.batch_size and not args.dry_run:
                    inserted = db.insert_batch(records_to_insert)
                    logger.info(f"Inserted batch of {inserted} records")
                    records_to_insert = []
                    
            except Exception as e:
                logger.error(f"Error processing ID {record.id}: {e}")
                records_failed += 1
        
        # Insert remaining records
        if records_to_insert and not args.dry_run:
            inserted = db.insert_batch(records_to_insert)
            logger.info(f"Inserted final batch of {inserted} records")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        processor.cleanup()
        embedding_service.close()
    
    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("=" * 60)
    logger.info("Ingestion Complete")
    logger.info("=" * 60)
    logger.info(f"Records processed: {records_processed}")
    logger.info(f"Records failed: {records_failed}")
    logger.info(f"Total time: {duration:.2f} seconds")
    
    if not args.dry_run:
        try:
            total_records = db.get_record_count()
            logger.info(f"Total records in database: {total_records}")
        except:
            pass
    else:
        logger.info("(Dry run - no data inserted)")
    
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
