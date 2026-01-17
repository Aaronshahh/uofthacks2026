"""
RAG query routes for the Footwear RAG Agent.
"""

import logging
from fastapi import APIRouter, HTTPException, UploadFile, File

from ..models import RAGQueryResponse, CasesResponse, MetadataCaseResponse, QueryMetadataResponse, ErrorResponse
from ..rag_query import RAGQueryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["query"])


@router.post(
    "/query",
    response_model=RAGQueryResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="RAG query with image",
    description="Upload a footprint image to find the top 3 closest matches and their metadata"
)
async def query_footprint(
    image: UploadFile = File(..., description="Footprint image file (TIFF, PNG, or JPEG)")
):
    """
    Execute a RAG query with an uploaded footprint image.
    
    This endpoint:
    1. Receives an image upload
    2. Generates an embedding for the image
    3. Finds the top 3 closest matches in the database
    4. Returns 3 metadata cases (CASE A, CASE B, CASE C)
    
    Returns:
        RAGQueryResponse with 3 possible metadata cases
    """
    # Validate file type
    allowed_types = ["image/tiff", "image/png", "image/jpeg", "image/jpg"]
    content_type = image.content_type or ""
    
    # Also check file extension as fallback
    filename = image.filename or ""
    allowed_extensions = [".tiff", ".tif", ".png", ".jpg", ".jpeg"]
    has_valid_extension = any(filename.lower().endswith(ext) for ext in allowed_extensions)
    
    if content_type not in allowed_types and not has_valid_extension:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: TIFF, PNG, JPEG. Got: {content_type}"
        )
    
    try:
        # Read image data
        image_data = await image.read()
        
        if not image_data:
            raise HTTPException(status_code=400, detail="Empty image file")
        
        # Execute RAG query - use local embeddings to match database (512-dim)
        rag_service = RAGQueryService()
        result = rag_service.query(image_data, use_snowflake_embeddings=False)
        
        # Convert to response model
        cases_dict = result.to_dict()["cases"]
        
        cases_response = CasesResponse(
            case_a=MetadataCaseResponse(**cases_dict["case_a"]) if cases_dict.get("case_a") else None,
            case_b=MetadataCaseResponse(**cases_dict["case_b"]) if cases_dict.get("case_b") else None,
            case_c=MetadataCaseResponse(**cases_dict["case_c"]) if cases_dict.get("case_c") else None,
        )
        
        query_metadata = QueryMetadataResponse(**result.query_metadata)
        
        return RAGQueryResponse(
            cases=cases_response,
            query_metadata=query_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/query/local",
    response_model=RAGQueryResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="RAG query with local embedding",
    description="Upload a footprint image and use local embedding (fallback when Snowflake unavailable)"
)
async def query_footprint_local(
    image: UploadFile = File(..., description="Footprint image file")
):
    """
    Execute a RAG query using local embedding generation.
    
    Use this endpoint when Snowflake Cortex is unavailable.
    """
    try:
        image_data = await image.read()
        
        if not image_data:
            raise HTTPException(status_code=400, detail="Empty image file")
        
        # Execute RAG query with local embeddings
        rag_service = RAGQueryService()
        result = rag_service.query(image_data, use_snowflake_embeddings=False)
        
        # Convert to response model
        cases_dict = result.to_dict()["cases"]
        
        cases_response = CasesResponse(
            case_a=MetadataCaseResponse(**cases_dict["case_a"]) if cases_dict.get("case_a") else None,
            case_b=MetadataCaseResponse(**cases_dict["case_b"]) if cases_dict.get("case_b") else None,
            case_c=MetadataCaseResponse(**cases_dict["case_c"]) if cases_dict.get("case_c") else None,
        )
        
        query_metadata = QueryMetadataResponse(**result.query_metadata)
        
        return RAGQueryResponse(
            cases=cases_response,
            query_metadata=query_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
