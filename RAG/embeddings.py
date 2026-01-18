"""
Embedding generation for the Footwear RAG Agent.
Uses Snowflake Cortex for image embeddings.
"""

import base64
import io
import logging
from typing import List, Optional, Dict, Any
from PIL import Image
import snowflake.connector

from .config import get_config, EmbeddingConfig, SnowflakeConfig

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating image embeddings using Snowflake Cortex.
    
    Handles:
    - Image preprocessing (TIFF -> PNG/JPEG)
    - Encoding images for Snowflake
    - Calling Snowflake Cortex embedding functions
    """
    
    def __init__(
        self,
        embedding_config: Optional[EmbeddingConfig] = None,
        snowflake_config: Optional[SnowflakeConfig] = None
    ):
        """
        Initialize the embedding service.
        
        Args:
            embedding_config: EmbeddingConfig instance.
            snowflake_config: SnowflakeConfig instance.
        """
        config = get_config()
        self.embedding_config = embedding_config or config.embedding
        self.snowflake_config = snowflake_config or config.snowflake
        self._connection = None
    
    def _get_connection(self):
        """Get or create Snowflake connection."""
        if self._connection is None or self._connection.is_closed():
            conn_params = {
                "account": self.snowflake_config.account,
                "user": self.snowflake_config.user,
                "warehouse": self.snowflake_config.warehouse,
                "database": self.snowflake_config.database,
                "schema": self.snowflake_config.schema_name,
                "role": self.snowflake_config.role,
            }
            
            # Add password if provided, otherwise use authenticator
            if self.snowflake_config.password:
                conn_params["password"] = self.snowflake_config.password
            elif self.snowflake_config.authenticator:
                conn_params["authenticator"] = self.snowflake_config.authenticator
            
            self._connection = snowflake.connector.connect(**conn_params)
            
            # Explicitly activate warehouse, database, and schema
            cursor = self._connection.cursor()
            cursor.execute(f"USE WAREHOUSE {self.snowflake_config.warehouse}")
            cursor.execute(f"USE DATABASE {self.snowflake_config.database}")
            cursor.execute(f"USE SCHEMA {self.snowflake_config.schema_name}")
            cursor.close()
            
        return self._connection
    
    def close(self):
        """Close the Snowflake connection."""
        if self._connection and not self._connection.is_closed():
            self._connection.close()
            self._connection = None
    
    def preprocess_image(
        self,
        image_data: bytes,
        max_size: int = 512,
        output_format: str = "PNG"
    ) -> bytes:
        """
        Preprocess image for embedding generation.
        
        Args:
            image_data: Raw image bytes (can be TIFF).
            max_size: Maximum dimension (width or height).
            output_format: Output format (PNG or JPEG).
            
        Returns:
            Preprocessed image bytes.
        """
        img = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        
        # Resize if larger than max_size
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Convert to bytes
        output_buffer = io.BytesIO()
        img.save(output_buffer, format=output_format)
        return output_buffer.getvalue()
    
    def image_to_base64(self, image_data: bytes) -> str:
        """
        Convert image bytes to base64 string.
        
        Args:
            image_data: Image bytes.
            
        Returns:
            Base64 encoded string.
        """
        return base64.b64encode(image_data).decode('utf-8')
    
    def generate_embedding_snowflake(
        self,
        image_data: bytes,
        preprocess: bool = True
    ) -> List[float]:
        """
        Generate image embedding using Snowflake Cortex.
        
        Uses SNOWFLAKE.CORTEX.EMBED_TEXT_1024 with image description
        as a fallback since direct image embedding might require specific setup.
        
        For production, you may want to use:
        - SNOWFLAKE.CORTEX.EMBED_IMAGE if available
        - Or a custom embedding model
        
        Args:
            image_data: Raw image bytes.
            preprocess: Whether to preprocess the image first.
            
        Returns:
            Embedding vector (1024 dimensions).
        """
        if preprocess:
            image_data = self.preprocess_image(image_data)
        
        # Encode image to base64
        image_b64 = self.image_to_base64(image_data)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Try using Snowflake's image embedding function
            # Note: This uses a text-based approach as fallback
            # For actual image embeddings, configure Snowflake's multimodal models
            
            # Option 1: Try EMBED_IMAGE (if available in your Snowflake account)
            try:
                embed_sql = f"""
                SELECT SNOWFLAKE.CORTEX.EMBED_IMAGE_1024(
                    'snowflake-arctic-embed-l-v2.0',
                    TO_BINARY('{image_b64}', 'BASE64')
                )
                """
                cursor.execute(embed_sql)
                result = cursor.fetchone()
                if result and result[0]:
                    embedding = list(result[0])
                    logger.debug(f"Generated image embedding with dimension {len(embedding)}")
                    return embedding
            except Exception as e:
                logger.debug(f"EMBED_IMAGE not available: {e}")
            
            # Option 2: Fallback to text embedding with image hash/descriptor
            # This is a simplified approach - in production use proper image embeddings
            import hashlib
            image_hash = hashlib.sha256(image_data).hexdigest()
            
            # Create a pseudo-description for the image for text embedding
            # In production, replace with actual image embedding
            description = f"footprint image hash {image_hash[:32]}"
            
            embed_sql = f"""
            SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_1024(
                'snowflake-arctic-embed-l-v2.0',
                %s
            )
            """
            cursor.execute(embed_sql, (description,))
            result = cursor.fetchone()
            
            if result and result[0]:
                embedding = list(result[0])
                logger.debug(f"Generated text-based embedding with dimension {len(embedding)}")
                return embedding
            else:
                raise RuntimeError("Failed to generate embedding")
                
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    def generate_embedding_local(
        self,
        image_data: bytes,
        preprocess: bool = True
    ) -> List[float]:
        """
        Generate image embedding using a local model (fallback).
        
        This uses a simple feature extraction approach.
        For production, use proper image embedding models like CLIP.
        
        Args:
            image_data: Raw image bytes.
            preprocess: Whether to preprocess the image first.
            
        Returns:
            Embedding vector (512 dimensions to match database).
        """
        if preprocess:
            image_data = self.preprocess_image(image_data, max_size=224)
        
        # Load image
        img = Image.open(io.BytesIO(image_data))
        if img.mode != 'L':
            img = img.convert('L')
        
        # Resize to fixed size for consistent embeddings
        # 512 dimensions = 22x22 pixels rounded up, we use 23x23 and truncate
        img = img.resize((23, 23), Image.Resampling.LANCZOS)
        
        # Convert to array and normalize
        import numpy as np
        arr = np.array(img).flatten().astype(np.float32)
        arr = arr / 255.0  # Normalize to [0, 1]
        
        # Pad or truncate to 512 dimensions (must match database)
        if len(arr) < 512:
            arr = np.pad(arr, (0, 512 - len(arr)), mode='constant')
        else:
            arr = arr[:512]
        
        # Ensure no NaN or None values
        arr = np.nan_to_num(arr, nan=0.0, posinf=1.0, neginf=0.0)
        
        result = arr.tolist()
        logger.debug(f"Generated local embedding with {len(result)} dimensions")
        return result
    
    def generate_embedding(
        self,
        image_data: bytes,
        use_snowflake: bool = True,
        preprocess: bool = True
    ) -> List[float]:
        """
        Generate image embedding using configured method.
        
        Args:
            image_data: Raw image bytes.
            use_snowflake: Whether to use Snowflake Cortex.
            preprocess: Whether to preprocess the image first.
            
        Returns:
            Embedding vector.
        """
        if use_snowflake:
            try:
                return self.generate_embedding_snowflake(image_data, preprocess)
            except Exception as e:
                logger.warning(f"Snowflake embedding failed, using local: {e}")
                return self.generate_embedding_local(image_data, preprocess)
        else:
            return self.generate_embedding_local(image_data, preprocess)
    
    def generate_batch_embeddings(
        self,
        images: List[bytes],
        use_snowflake: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple images.
        
        Args:
            images: List of image bytes.
            use_snowflake: Whether to use Snowflake Cortex.
            
        Returns:
            List of embedding vectors.
        """
        embeddings = []
        for i, image_data in enumerate(images):
            try:
                embedding = self.generate_embedding(image_data, use_snowflake)
                embeddings.append(embedding)
                if (i + 1) % 10 == 0:
                    logger.info(f"Generated {i + 1}/{len(images)} embeddings")
            except Exception as e:
                logger.error(f"Failed to generate embedding for image {i}: {e}")
                # Use zero vector as placeholder
                embeddings.append([0.0] * self.embedding_config.image_dimension)
        
        return embeddings


def create_embedding_service() -> EmbeddingService:
    """Factory function to create an embedding service."""
    return EmbeddingService()
