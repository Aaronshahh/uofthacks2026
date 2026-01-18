"""
RAG Query logic for the Footwear RAG Agent.
Implements top-3 retrieval and formats metadata as separate cases.
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from .database import SnowflakeVectorDB, SearchResult, average_embeddings
from .embeddings import EmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class MetadataCase:
    """Represents a single metadata case from the RAG results."""
    case_label: str  # "CASE A", "CASE B", "CASE C"
    id: str
    metadata: Dict[str, Any]
    similarity_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "case_label": self.case_label,
            "id": self.id,
            "metadata": self.metadata,
            "similarity_score": self.similarity_score
        }


@dataclass
class RAGQueryResult:
    """Result from a RAG query."""
    cases: List[MetadataCase]
    query_metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "cases": {
                "case_a": self.cases[0].to_dict() if len(self.cases) > 0 else None,
                "case_b": self.cases[1].to_dict() if len(self.cases) > 1 else None,
                "case_c": self.cases[2].to_dict() if len(self.cases) > 2 else None,
            },
            "query_metadata": self.query_metadata
        }


class RAGQueryService:
    """
    Service for executing RAG queries on the footprint database.
    
    Query Flow:
    1. Embed the input image
    2. Find top 3 closest image embeddings using vector similarity
    3. Average the 3 embeddings (for internal use)
    4. Format metadata from top 3 as separate cases (CASE A, B, C)
    """
    
    CASE_LABELS = ["CASE A", "CASE B", "CASE C"]
    
    def __init__(
        self,
        db: Optional[SnowflakeVectorDB] = None,
        embedding_service: Optional[EmbeddingService] = None
    ):
        """
        Initialize the RAG query service.
        
        Args:
            db: SnowflakeVectorDB instance.
            embedding_service: EmbeddingService instance.
        """
        self.db = db or SnowflakeVectorDB()
        self.embedding_service = embedding_service or EmbeddingService()
    
    def query(
        self,
        image_data: bytes,
        use_snowflake_embeddings: bool = False  # Use local by default to match 512-dim database
    ) -> RAGQueryResult:
        """
        Execute a RAG query with an input image.
        
        Args:
            image_data: Raw image bytes.
            use_snowflake_embeddings: Whether to use Snowflake for embeddings.
            
        Returns:
            RAGQueryResult with 3 metadata cases.
        """
        start_time = datetime.now()
        
        # Step 1: Generate embedding for the query image
        logger.info("Generating embedding for query image...")
        query_embedding = self.embedding_service.generate_embedding(
            image_data,
            use_snowflake=use_snowflake_embeddings
        )
        
        # Step 2: Find top 3 closest vectors and get their embeddings
        logger.info("Searching for top 3 similar footprints...")
        search_results, result_embeddings = self.db.get_top3_with_embeddings(query_embedding)
        
        if not search_results:
            logger.warning("No results found in database")
            return RAGQueryResult(
                cases=[],
                query_metadata={
                    "timestamp": datetime.now().isoformat(),
                    "embedding_model": "snowflake_native" if use_snowflake_embeddings else "local",
                    "results_found": 0,
                    "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000
                }
            )
        
        # Step 3: Average embeddings (for internal use - could be used for re-ranking or caching)
        if result_embeddings:
            target_embedding = average_embeddings(result_embeddings)
            logger.debug(f"Computed target embedding from {len(result_embeddings)} vectors")
        else:
            target_embedding = None
        
        # Step 4: Format results as metadata cases
        cases = self._format_as_cases(search_results)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return RAGQueryResult(
            cases=cases,
            query_metadata={
                "timestamp": datetime.now().isoformat(),
                "embedding_model": "snowflake_native" if use_snowflake_embeddings else "local",
                "results_found": len(cases),
                "processing_time_ms": round(processing_time, 2)
            }
        )
    
    def _format_as_cases(self, search_results: List[SearchResult]) -> List[MetadataCase]:
        """
        Format search results as labeled metadata cases.
        
        Args:
            search_results: List of SearchResult from database.
            
        Returns:
            List of MetadataCase objects (CASE A, CASE B, CASE C).
        """
        cases = []
        
        for i, result in enumerate(search_results[:3]):  # Max 3 cases
            case = MetadataCase(
                case_label=self.CASE_LABELS[i],
                id=result.id,
                metadata=result.metadata,
                similarity_score=round(result.similarity_score, 4)
            )
            cases.append(case)
        
        return cases
    
    def query_with_embedding(
        self,
        query_embedding: List[float]
    ) -> RAGQueryResult:
        """
        Execute a RAG query with a pre-computed embedding.
        
        Args:
            query_embedding: Pre-computed embedding vector.
            
        Returns:
            RAGQueryResult with 3 metadata cases.
        """
        start_time = datetime.now()
        
        # Find top 3 closest vectors
        search_results, result_embeddings = self.db.get_top3_with_embeddings(query_embedding)
        
        if not search_results:
            return RAGQueryResult(
                cases=[],
                query_metadata={
                    "timestamp": datetime.now().isoformat(),
                    "embedding_model": "pre-computed",
                    "results_found": 0,
                    "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000
                }
            )
        
        # Format results as cases
        cases = self._format_as_cases(search_results)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return RAGQueryResult(
            cases=cases,
            query_metadata={
                "timestamp": datetime.now().isoformat(),
                "embedding_model": "pre-computed",
                "results_found": len(cases),
                "processing_time_ms": round(processing_time, 2)
            }
        )


def format_cases_for_display(result: RAGQueryResult) -> str:
    """
    Format RAG query result for text display.
    
    Args:
        result: RAGQueryResult object.
        
    Returns:
        Formatted string for display.
    """
    if not result.cases:
        return "No matching footprints found."
    
    lines = [
        f"Found {len(result.cases)} possible cases:",
        ""
    ]
    
    for case in result.cases:
        lines.append(f"=== {case.case_label} ===")
        lines.append(f"ID: {case.id}")
        lines.append(f"Similarity Score: {case.similarity_score:.4f}")
        lines.append("Metadata:")
        
        for key, value in case.metadata.items():
            lines.append(f"  - {key}: {value}")
        
        lines.append("")
    
    lines.append(f"Query processed at: {result.query_metadata.get('timestamp', 'N/A')}")
    lines.append(f"Processing time: {result.query_metadata.get('processing_time_ms', 0):.2f}ms")
    
    return "\n".join(lines)
