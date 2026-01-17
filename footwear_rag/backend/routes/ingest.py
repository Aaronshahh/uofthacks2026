"""
Data ingestion routes for the Footwear RAG Agent.
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException

from ..models import IngestRequest, IngestResponse, ErrorResponse
from ..data_processor import DataProcessor
from ..database import SnowflakeVectorDB
from ..embeddings import EmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["ingestion"])


@router.post(
    "/ingest",
    response_model=IngestResponse,
    responses={
        500: {"model": ErrorResponse}
    },
    summary="Ingest footprint data",
    description="Process zip files and CSV metadata, generate embeddings, and store in Snowflake"
)
async def ingest_data(request: IngestRequest = None):
    """
    Ingest footprint data from zip files and CSV.
    
    This endpoint:
    1. Extracts images from zip files
    2. Parses CSV metadata
    3. Matches images to metadata by ID
    4. Generates embeddings for each image
    5. Stores embeddings and metadata in Snowflake
    """
    if request is None:
        request = IngestRequest()
    
    start_time = datetime.now()
    errors = []
    
    try:
        # Initialize services
        processor = DataProcessor()
        db = SnowflakeVectorDB()
        embedding_service = EmbeddingService()
        
        # Create table if needed
        db.create_table(drop_existing=request.drop_existing)
        
        # Process data
        logger.info("Starting data ingestion...")
        records_processed = 0
        records_to_insert = []
        
        for record in processor.process_all(
            zip_directory=request.zip_directory,
            csv_path=request.csv_file
        ):
            try:
                # Validate image
                if not processor.validate_image(record.image_data):
                    errors.append(f"Invalid image for ID {record.id}")
                    continue
                
                # Generate embedding - use local to match 512-dim database schema
                embedding = embedding_service.generate_embedding(
                    record.image_data,
                    use_snowflake=False
                )
                
                records_to_insert.append({
                    "id": record.id,
                    "image_path": record.image_path,
                    "metadata": record.metadata,
                    "embedding": embedding
                })
                
                records_processed += 1
                
                if records_processed % 50 == 0:
                    logger.info(f"Processed {records_processed} records...")
                    
            except Exception as e:
                errors.append(f"Error processing ID {record.id}: {str(e)}")
                logger.error(f"Error processing {record.id}: {e}")
        
        # Batch insert
        records_inserted = 0
        if records_to_insert:
            records_inserted = db.insert_batch(records_to_insert)
        
        # Cleanup
        processor.cleanup()
        embedding_service.close()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return IngestResponse(
            status="completed",
            records_processed=records_processed,
            records_inserted=records_inserted,
            errors=errors[:10],  # Limit errors in response
            processing_time_seconds=round(processing_time, 2)
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/ingest/status",
    response_model=dict,
    summary="Get ingestion status",
    description="Get the current status of the database"
)
async def get_ingest_status():
    """Get current database status and record count."""
    try:
        db = SnowflakeVectorDB()
        count = db.get_record_count()
        
        return {
            "status": "ready",
            "record_count": count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
