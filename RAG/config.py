"""
Configuration module for RAG system.
Loads configuration from environment variables (.env file).
"""

import os
import logging
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


@dataclass
class SnowflakeConfig:
    """Snowflake connection configuration."""
    account: str
    user: str
    password: Optional[str] = None
    authenticator: Optional[str] = None
    warehouse: str = "COMPUTE_WH"
    database: str = "EVIDENCE_DB"
    schema_name: str = "PUBLIC"
    role: str = "ACCOUNTADMIN"


@dataclass
class EmbeddingConfig:
    """Embedding generation configuration."""
    model: str = "sentence-transformers/all-MiniLM-L6-v2"
    use_snowflake: bool = False


@dataclass
class Config:
    """Main configuration class."""
    snowflake: SnowflakeConfig
    embedding: EmbeddingConfig


def get_config() -> Config:
    """
    Load configuration from environment variables.
    
    Returns:
        Config object with all settings.
        
    Raises:
        ValueError: If required Snowflake configuration is missing.
    """
    # Snowflake configuration
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    username = os.getenv("SNOWFLAKE_USERNAME")
    password = os.getenv("SNOWFLAKE_PASSWORD")
    authenticator = os.getenv("SNOWFLAKE_AUTHENTICATOR")
    
    # Validate required fields
    if not account or not username:
        raise ValueError(
            "Missing required Snowflake configuration. "
            "Please set SNOWFLAKE_ACCOUNT and SNOWFLAKE_USERNAME in .env file."
        )
    
    # At least one authentication method must be provided
    if not password and not authenticator:
        raise ValueError(
            "Missing Snowflake authentication. "
            "Please provide either SNOWFLAKE_PASSWORD or SNOWFLAKE_AUTHENTICATOR in .env file."
        )
    
    snowflake_config = SnowflakeConfig(
        account=account,
        user=username,
        password=password,
        authenticator=authenticator,
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        database=os.getenv("SNOWFLAKE_DATABASE", "EVIDENCE_DB"),
        schema_name=os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
        role=os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
    )
    
    embedding_config = EmbeddingConfig(
        model=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        use_snowflake=os.getenv("USE_SNOWFLAKE_EMBEDDINGS", "false").lower() == "true",
    )
    
    return Config(
        snowflake=snowflake_config,
        embedding=embedding_config,
    )
