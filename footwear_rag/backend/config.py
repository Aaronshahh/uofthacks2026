"""
Configuration management for the Footwear RAG Agent.
Loads settings from config/config.yaml and environment variables.
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import yaml
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()


class SnowflakeConfig(BaseModel):
    """Snowflake connection configuration."""
    account: str = Field(..., description="Snowflake account identifier")
    user: str = Field(..., description="Snowflake username")
    password: str = Field(default="", description="Snowflake password (optional if using authenticator)")
    authenticator: Optional[str] = Field(default=None, description="Authenticator type (e.g., 'externalbrowser')")
    warehouse: str = Field(..., description="Snowflake warehouse name")
    database: str = Field(..., description="Snowflake database name")
    schema_name: str = Field(..., alias="schema", description="Snowflake schema name")
    role: str = Field(..., description="Snowflake role")


class DataConfig(BaseModel):
    """Data paths configuration."""
    zip_directory: str = Field(..., description="Path to zip files directory")
    csv_file: str = Field(..., description="Path to metadata CSV file")
    image_extensions: List[str] = Field(
        default=[".tiff", ".tif"],
        description="Allowed image file extensions"
    )
    id_column: str = Field(default="id", description="CSV column name for matching IDs")


class EmbeddingConfig(BaseModel):
    """Embedding configuration."""
    model: str = Field(default="snowflake_native", description="Embedding model to use")
    image_dimension: int = Field(default=1024, description="Embedding vector dimension")


class APIConfig(BaseModel):
    """API server configuration."""
    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")


class Config(BaseModel):
    """Main configuration container."""
    snowflake: SnowflakeConfig
    data: DataConfig
    embedding: EmbeddingConfig
    api: APIConfig


def get_project_root() -> Path:
    """Get the project root directory."""
    # Navigate up from backend/config.py to find project root
    current = Path(__file__).resolve()
    # Go up: config.py -> backend -> footwear_rag -> project_root
    return current.parent.parent.parent


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from YAML file and environment variables.
    
    Environment variables override config file values:
    - SNOWFLAKE_ACCOUNT
    - SNOWFLAKE_USER
    - SNOWFLAKE_PASSWORD
    - SNOWFLAKE_WAREHOUSE
    - SNOWFLAKE_DATABASE
    - SNOWFLAKE_SCHEMA
    - SNOWFLAKE_ROLE
    
    Args:
        config_path: Optional path to config file. Defaults to config/config.yaml
        
    Returns:
        Config object with all settings
    """
    project_root = get_project_root()
    
    if config_path is None:
        config_path = project_root / "config" / "config.yaml"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)
    
    # Override Snowflake config with environment variables if present
    snowflake_env_mapping = {
        "account": "SNOWFLAKE_ACCOUNT",
        "user": "SNOWFLAKE_USER",
        "password": "SNOWFLAKE_PASSWORD",
        "warehouse": "SNOWFLAKE_WAREHOUSE",
        "database": "SNOWFLAKE_DATABASE",
        "schema": "SNOWFLAKE_SCHEMA",
        "role": "SNOWFLAKE_ROLE",
    }
    
    for config_key, env_var in snowflake_env_mapping.items():
        env_value = os.getenv(env_var)
        if env_value:
            config_data["snowflake"][config_key] = env_value
    
    # Resolve relative paths to absolute paths
    if not Path(config_data["data"]["zip_directory"]).is_absolute():
        config_data["data"]["zip_directory"] = str(
            project_root / config_data["data"]["zip_directory"]
        )
    
    if not Path(config_data["data"]["csv_file"]).is_absolute():
        config_data["data"]["csv_file"] = str(
            project_root / config_data["data"]["csv_file"]
        )
    
    return Config(**config_data)


# Global config instance (lazy loaded)
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config(config_path: Optional[str] = None) -> Config:
    """Reload configuration from file."""
    global _config
    _config = load_config(config_path)
    return _config
