"""
Snowflake database operations for the Footwear RAG Agent.
Handles connection, table creation, and vector operations.
"""

import json
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np
import snowflake.connector
from snowflake.connector import SnowflakeConnection
from contextlib import contextmanager

from .config import get_config, SnowflakeConfig

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Result from a vector similarity search."""
    id: str
    metadata: Dict
    similarity_score: float


class SnowflakeVectorDB:
    """
    Snowflake vector database operations.
    
    Handles:
    - Connection management
    - Table creation and schema
    - Vector insertion and search
    - Top-k retrieval for RAG queries
    """
    
    TABLE_NAME = "FOOTPRINT_VECTORS"
    VECTOR_DIMENSION = 512  # Must match the dimension in the database
    
    def __init__(self, config: Optional[SnowflakeConfig] = None):
        """
        Initialize the Snowflake vector database.
        
        Args:
            config: SnowflakeConfig instance. If None, loads from global config.
        """
        if config is None:
            config = get_config().snowflake
        self.config = config
        self._connection: Optional[SnowflakeConnection] = None
    
    def _get_connection_params(self) -> Dict[str, str]:
        """Get connection parameters from config."""
        params = {
            "account": self.config.account,
            "user": self.config.user,
            "warehouse": self.config.warehouse,
            "database": self.config.database,
            "schema": self.config.schema_name,
            "role": self.config.role,
        }
        
        # Add password if provided, otherwise use authenticator
        if self.config.password:
            params["password"] = self.config.password
        elif self.config.authenticator:
            params["authenticator"] = self.config.authenticator
        
        return params
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            SnowflakeConnection instance.
        """
        conn = snowflake.connector.connect(**self._get_connection_params())
        try:
            # Explicitly activate warehouse, database, and schema
            cursor = conn.cursor()
            cursor.execute(f"USE WAREHOUSE {self.config.warehouse}")
            cursor.execute(f"USE DATABASE {self.config.database}")
            cursor.execute(f"USE SCHEMA {self.config.schema_name}")
            cursor.close()
            yield conn
        finally:
            conn.close()
    
    def connect(self) -> SnowflakeConnection:
        """
        Establish a persistent connection.
        
        Returns:
            SnowflakeConnection instance.
        """
        if self._connection is None or self._connection.is_closed():
            self._connection = snowflake.connector.connect(**self._get_connection_params())
            logger.info("Connected to Snowflake")
        return self._connection
    
    def disconnect(self):
        """Close the persistent connection."""
        if self._connection and not self._connection.is_closed():
            self._connection.close()
            self._connection = None
            logger.info("Disconnected from Snowflake")
    
    def create_table(self, drop_existing: bool = False):
        """
        Create the footprint vectors table.
        
        Args:
            drop_existing: If True, drops existing table first.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if drop_existing:
                cursor.execute(f"DROP TABLE IF EXISTS {self.TABLE_NAME}")
                logger.info(f"Dropped existing table {self.TABLE_NAME}")
            
            # Create table with vector column
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                id VARCHAR PRIMARY KEY,
                image_path VARCHAR,
                metadata VARIANT,
                image_embedding VECTOR(FLOAT, {self.VECTOR_DIMENSION}),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
            )
            """
            cursor.execute(create_sql)
            conn.commit()
            logger.info(f"Created table {self.TABLE_NAME}")
    
    def insert_record(
        self,
        id: str,
        image_path: str,
        metadata: Dict,
        embedding: List[float]
    ):
        """
        Insert a single footprint record.
        
        Args:
            id: Unique identifier for the record.
            image_path: Path/reference to the original image.
            metadata: Dictionary of metadata (age, weight, height, gender, etc.).
            embedding: Image embedding vector.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Convert embedding to Snowflake vector format
            embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
            metadata_json = json.dumps(metadata)
            
            insert_sql = f"""
            INSERT INTO {self.TABLE_NAME} (id, image_path, metadata, image_embedding)
            SELECT 
                %s,
                %s,
                PARSE_JSON(%s),
                {embedding_str}::VECTOR(FLOAT, {self.VECTOR_DIMENSION})
            """
            
            cursor.execute(insert_sql, (id, image_path, metadata_json))
            conn.commit()
    
    def insert_batch(
        self,
        records: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> int:
        """
        Insert multiple records in batches.
        
        Args:
            records: List of dicts with keys: id, image_path, metadata, embedding
            batch_size: Number of records per batch.
            
        Returns:
            Number of records inserted.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            inserted = 0
            
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                
                for record in batch:
                    try:
                        embedding_str = "[" + ",".join(str(v) for v in record["embedding"]) + "]"
                        metadata_json = json.dumps(record["metadata"])
                        
                        insert_sql = f"""
                        INSERT INTO {self.TABLE_NAME} (id, image_path, metadata, image_embedding)
                        SELECT 
                            %s,
                            %s,
                            PARSE_JSON(%s),
                            {embedding_str}::VECTOR(FLOAT, {self.VECTOR_DIMENSION})
                        """
                        
                        cursor.execute(insert_sql, (
                            record["id"],
                            record["image_path"],
                            metadata_json
                        ))
                        inserted += 1
                    except Exception as e:
                        logger.error(f"Failed to insert record {record.get('id')}: {e}")
                
                conn.commit()
                logger.info(f"Inserted batch {i // batch_size + 1}, total: {inserted}")
            
            return inserted
    
    def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 3
    ) -> List[SearchResult]:
        """
        Search for similar footprints using vector similarity.
        
        Args:
            query_embedding: Query image embedding vector.
            top_k: Number of results to return.
            
        Returns:
            List of SearchResult objects with metadata and similarity scores.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Convert query embedding to Snowflake vector format
            embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"
            
            # Use cosine similarity for vector search
            search_sql = f"""
            SELECT 
                id,
                metadata,
                VECTOR_COSINE_SIMILARITY(
                    image_embedding,
                    {embedding_str}::VECTOR(FLOAT, {self.VECTOR_DIMENSION})
                ) as similarity
            FROM {self.TABLE_NAME}
            ORDER BY similarity DESC
            LIMIT {top_k}
            """
            
            cursor.execute(search_sql)
            results = cursor.fetchall()
            
            search_results = []
            for row in results:
                result = SearchResult(
                    id=row[0],
                    metadata=json.loads(row[1]) if isinstance(row[1], str) else row[1],
                    similarity_score=float(row[2])
                )
                search_results.append(result)
            
            return search_results
    
    def get_top3_with_embeddings(
        self,
        query_embedding: List[float]
    ) -> Tuple[List[SearchResult], List[List[float]]]:
        """
        Get top 3 similar records along with their embeddings.
        
        Used for the RAG query mechanism to compute averaged embedding.
        
        Args:
            query_embedding: Query image embedding vector.
            
        Returns:
            Tuple of (list of SearchResult, list of embeddings for averaging)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Ensure all embedding values are valid floats (no None values)
            clean_embedding = [float(v) if v is not None else 0.0 for v in query_embedding]
            embedding_str = "[" + ",".join(str(v) for v in clean_embedding) + "]"
            
            search_sql = f"""
            SELECT 
                id,
                metadata,
                image_embedding,
                VECTOR_COSINE_SIMILARITY(
                    image_embedding,
                    {embedding_str}::VECTOR(FLOAT, {self.VECTOR_DIMENSION})
                ) as similarity
            FROM {self.TABLE_NAME}
            WHERE image_embedding IS NOT NULL
            ORDER BY similarity DESC
            LIMIT 3
            """
            
            cursor.execute(search_sql)
            results = cursor.fetchall()
            
            search_results = []
            embeddings = []
            
            for row in results:
                # Handle potential None similarity score
                similarity = row[3]
                if similarity is None:
                    logger.warning(f"Null similarity for record {row[0]}, skipping")
                    continue
                    
                result = SearchResult(
                    id=row[0],
                    metadata=json.loads(row[1]) if isinstance(row[1], str) else row[1],
                    similarity_score=float(similarity)
                )
                search_results.append(result)
                
                # Parse embedding from result
                emb = row[2]
                if isinstance(emb, str):
                    # Parse string format "[1.0, 2.0, ...]"
                    emb = json.loads(emb)
                if emb is not None:
                    embeddings.append(list(emb))
            
            return search_results, embeddings
    
    def get_record_count(self) -> int:
        """Get the total number of records in the table."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {self.TABLE_NAME}")
            result = cursor.fetchone()
            return result[0] if result else 0
    
    def delete_record(self, id: str):
        """Delete a record by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {self.TABLE_NAME} WHERE id = %s", (id,))
            conn.commit()
    
    def clear_table(self):
        """Delete all records from the table."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"TRUNCATE TABLE {self.TABLE_NAME}")
            conn.commit()
            logger.info(f"Cleared all records from {self.TABLE_NAME}")


def average_embeddings(embeddings: List[List[float]]) -> List[float]:
    """
    Compute element-wise average of multiple embeddings.
    
    Args:
        embeddings: List of embedding vectors (each same dimension).
        
    Returns:
        Averaged embedding vector.
    """
    if not embeddings:
        raise ValueError("Cannot average empty list of embeddings")
    
    # Convert to numpy for efficient averaging
    emb_array = np.array(embeddings)
    avg = np.mean(emb_array, axis=0)
    
    return avg.tolist()
