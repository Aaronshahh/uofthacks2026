"""
Pydantic models for API request/response validation.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ============== Request Models ==============

class IngestRequest(BaseModel):
    """Request to ingest data from configured paths."""
    zip_directory: Optional[str] = Field(
        None,
        description="Path to zip files directory (uses config default if not provided)"
    )
    csv_file: Optional[str] = Field(
        None,
        description="Path to metadata CSV file (uses config default if not provided)"
    )
    drop_existing: bool = Field(
        False,
        description="Whether to drop existing data before ingestion"
    )


# ============== Response Models ==============

class MetadataCaseResponse(BaseModel):
    """A single metadata case from RAG query results."""
    case_label: str = Field(..., description="Case label (CASE A, CASE B, or CASE C)")
    id: str = Field(..., description="Record ID from database")
    metadata: Dict[str, Any] = Field(..., description="Full metadata dictionary")
    similarity_score: float = Field(..., description="Cosine similarity score (0-1)")


class CasesResponse(BaseModel):
    """Container for all 3 metadata cases."""
    case_a: Optional[MetadataCaseResponse] = Field(None, description="Top 1 match")
    case_b: Optional[MetadataCaseResponse] = Field(None, description="Top 2 match")
    case_c: Optional[MetadataCaseResponse] = Field(None, description="Top 3 match")


class QueryMetadataResponse(BaseModel):
    """Metadata about the query execution."""
    timestamp: str = Field(..., description="Query timestamp (ISO format)")
    embedding_model: str = Field(..., description="Embedding model used")
    results_found: int = Field(..., description="Number of results found")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class RAGQueryResponse(BaseModel):
    """Response from the RAG query endpoint."""
    cases: CasesResponse = Field(..., description="3 possible metadata cases")
    query_metadata: QueryMetadataResponse = Field(..., description="Query execution metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "cases": {
                    "case_a": {
                        "case_label": "CASE A",
                        "id": "FP001",
                        "metadata": {
                            "age": 35,
                            "weight": 75.5,
                            "height": 175,
                            "gender": "male"
                        },
                        "similarity_score": 0.9542
                    },
                    "case_b": {
                        "case_label": "CASE B",
                        "id": "FP042",
                        "metadata": {
                            "age": 42,
                            "weight": 82.0,
                            "height": 180,
                            "gender": "male"
                        },
                        "similarity_score": 0.9123
                    },
                    "case_c": {
                        "case_label": "CASE C",
                        "id": "FP087",
                        "metadata": {
                            "age": 29,
                            "weight": 68.0,
                            "height": 168,
                            "gender": "female"
                        },
                        "similarity_score": 0.8891
                    }
                },
                "query_metadata": {
                    "timestamp": "2026-01-17T10:30:00",
                    "embedding_model": "snowflake_native",
                    "results_found": 3,
                    "processing_time_ms": 125.5
                }
            }
        }


class IngestResponse(BaseModel):
    """Response from the ingest endpoint."""
    status: str = Field(..., description="Ingestion status")
    records_processed: int = Field(..., description="Number of records processed")
    records_inserted: int = Field(..., description="Number of records inserted")
    errors: List[str] = Field(default=[], description="List of errors encountered")
    processing_time_seconds: float = Field(..., description="Total processing time")


class HealthResponse(BaseModel):
    """Response from the health check endpoint."""
    status: str = Field(..., description="Service status")
    database_connected: bool = Field(..., description="Whether database is connected")
    record_count: int = Field(..., description="Number of records in database")
    timestamp: str = Field(..., description="Health check timestamp")


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
