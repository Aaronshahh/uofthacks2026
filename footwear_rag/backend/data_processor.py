"""
Data processing pipeline for the Footwear RAG Agent.
Handles extraction of images from zip files and matching with metadata from CSV or Excel files.
"""

import os
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Generator
from dataclasses import dataclass
import pandas as pd
from PIL import Image
import io
import logging

from .config import get_config, DataConfig

logger = logging.getLogger(__name__)


@dataclass
class FootprintRecord:
    """Represents a footprint image with its metadata."""
    id: str
    image_path: str
    image_data: bytes
    metadata: Dict


class DataProcessor:
    """
    Processes footprint data from zip files and metadata files.
    
    - Extracts .tiff images from zip files
    - Parses metadata from CSV or Excel files (.csv, .xlsx, .xls)
    - Matches images to metadata by ID
    """
    
    def __init__(self, config: Optional[DataConfig] = None):
        """
        Initialize the data processor.
        
        Args:
            config: DataConfig instance. If None, loads from global config.
        """
        if config is None:
            config = get_config().data
        self.config = config
        self._temp_dirs: List[str] = []
    
    def __del__(self):
        """Cleanup temporary directories."""
        self.cleanup()
    
    def cleanup(self):
        """Remove all temporary directories created during processing."""
        for temp_dir in self._temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        self._temp_dirs.clear()
    
    def _extract_metadata_id(self, image_filename: str) -> str:
        """
        Extract the metadata ID from an image filename.
        
        Image filename format: XXX_YY_L/R_NN (e.g., 001_01_L_01)
        Metadata ID format: XXX_YY (e.g., 001_01)
        
        Args:
            image_filename: Filename stem without extension.
            
        Returns:
            Extracted metadata ID (first two underscore-separated parts).
        """
        parts = image_filename.split('_')
        if len(parts) >= 2:
            # Join first two parts: XXX_YY
            return '_'.join(parts[:2])
        return image_filename  # Fallback to full name
    
    def load_csv_metadata(self, csv_path: Optional[str] = None) -> pd.DataFrame:
        """
        Load and parse the metadata file (CSV or Excel).
        
        Supports both .csv and .xlsx files.
        
        Args:
            csv_path: Path to metadata file. Uses config path if not provided.
            
        Returns:
            DataFrame with metadata, indexed by ID column.
        """
        if csv_path is None:
            csv_path = self.config.csv_file
        
        file_path = Path(csv_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {file_path}")
        
        # Read file based on extension
        file_ext = file_path.suffix.lower()
        if file_ext in ['.xlsx', '.xls']:
            # Read Excel file
            try:
                df = pd.read_excel(file_path, engine='openpyxl')
            except ImportError:
                raise ImportError(
                    "openpyxl is required to read Excel files. "
                    "Install it with: pip install openpyxl"
                )
        elif file_ext == '.csv':
            # Read CSV file
            df = pd.read_csv(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}. Supported: .csv, .xlsx, .xls")
        
        # Find the ID column
        id_column = self.config.id_column
        if id_column not in df.columns:
            # Try to find a column that looks like an ID
            possible_id_cols = ['id', 'ID', 'Id', 'image_id', 'filename', 'name']
            for col in possible_id_cols:
                if col in df.columns:
                    id_column = col
                    logger.info(f"Using '{col}' as ID column")
                    break
            else:
                # Use first column as ID
                id_column = df.columns[0]
                logger.warning(f"ID column '{self.config.id_column}' not found. Using '{id_column}'")
        
        # Convert ID column to string for matching
        df[id_column] = df[id_column].astype(str)
        
        # Set index to ID column for easy lookup
        df = df.set_index(id_column)
        
        logger.info(f"Loaded {len(df)} metadata records from {file_path}")
        logger.info(f"Columns: {list(df.columns)}")
        
        return df
    
    def extract_images_from_zip(self, zip_path: str) -> Generator[Tuple[str, bytes], None, None]:
        """
        Extract images from a zip file.
        
        Args:
            zip_path: Path to the zip file.
            
        Yields:
            Tuple of (image_id, image_bytes) for each valid image.
        """
        valid_extensions = set(ext.lower() for ext in self.config.image_extensions)
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for file_info in zf.infolist():
                if file_info.is_dir():
                    continue
                
                # Get file extension
                file_path = Path(file_info.filename)
                ext = file_path.suffix.lower()
                
                if ext not in valid_extensions:
                    continue
                
                # Extract image ID from filename (without extension)
                image_id = file_path.stem
                
                # Read image data
                try:
                    image_data = zf.read(file_info.filename)
                    yield image_id, image_data
                except Exception as e:
                    logger.error(f"Failed to read {file_info.filename}: {e}")
                    continue
    
    def get_all_zip_files(self, zip_directory: Optional[str] = None) -> List[str]:
        """
        Get all zip files in the specified directory.
        
        Args:
            zip_directory: Directory containing zip files. Uses config path if not provided.
            
        Returns:
            List of zip file paths.
        """
        if zip_directory is None:
            zip_directory = self.config.zip_directory
        
        zip_dir = Path(zip_directory)
        if not zip_dir.exists():
            raise FileNotFoundError(f"Zip directory not found: {zip_directory}")
        
        zip_files = list(zip_dir.glob("*.zip"))
        logger.info(f"Found {len(zip_files)} zip files in {zip_directory}")
        
        return [str(zf) for zf in zip_files]
    
    def process_all(
        self,
        zip_directory: Optional[str] = None,
        csv_path: Optional[str] = None
    ) -> Generator[FootprintRecord, None, None]:
        """
        Process all zip files and match with CSV metadata.
        
        Args:
            zip_directory: Directory containing zip files.
            csv_path: Path to metadata CSV file.
            
        Yields:
            FootprintRecord for each matched image-metadata pair.
        """
        # Load metadata
        metadata_df = self.load_csv_metadata(csv_path)
        
        # Get all zip files
        zip_files = self.get_all_zip_files(zip_directory)
        
        if not zip_files:
            logger.warning("No zip files found to process")
            return
        
        matched_count = 0
        unmatched_count = 0
        
        for zip_path in zip_files:
            logger.info(f"Processing {zip_path}")
            
            for image_id, image_data in self.extract_images_from_zip(zip_path):
                # Try to find matching metadata
                # Image filename format: XXX_YY_L/R_NN.tiff
                # Metadata ID format: XXX_YY
                # Extract the ID prefix (first two underscore-separated parts)
                metadata_id = self._extract_metadata_id(image_id)
                
                if metadata_id in metadata_df.index:
                    metadata = metadata_df.loc[metadata_id].to_dict()
                    
                    record = FootprintRecord(
                        id=image_id,  # Keep full image ID for uniqueness
                        image_path=f"{zip_path}:{image_id}",
                        image_data=image_data,
                        metadata=metadata
                    )
                    
                    matched_count += 1
                    yield record
                else:
                    unmatched_count += 1
                    logger.debug(f"No metadata found for image ID: {image_id} (extracted: {metadata_id})")
        
        logger.info(f"Processing complete. Matched: {matched_count}, Unmatched: {unmatched_count}")
    
    def process_all_to_list(
        self,
        zip_directory: Optional[str] = None,
        csv_path: Optional[str] = None
    ) -> List[FootprintRecord]:
        """
        Process all data and return as a list.
        
        Args:
            zip_directory: Directory containing zip files.
            csv_path: Path to metadata CSV file.
            
        Returns:
            List of FootprintRecord objects.
        """
        return list(self.process_all(zip_directory, csv_path))
    
    def validate_image(self, image_data: bytes) -> bool:
        """
        Validate that image data can be opened and processed.
        
        Args:
            image_data: Raw image bytes.
            
        Returns:
            True if image is valid, False otherwise.
        """
        try:
            img = Image.open(io.BytesIO(image_data))
            img.verify()
            return True
        except Exception as e:
            logger.debug(f"Image validation failed: {e}")
            return False
    
    def preprocess_image(
        self,
        image_data: bytes,
        max_size: int = 512,
        output_format: str = "PNG"
    ) -> bytes:
        """
        Preprocess image for embedding (resize, convert format).
        
        Args:
            image_data: Raw image bytes.
            max_size: Maximum dimension (width or height).
            output_format: Output image format.
            
        Returns:
            Preprocessed image bytes.
        """
        img = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary (TIFF might have different modes)
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        
        # Resize if larger than max_size
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Save to bytes
        output_buffer = io.BytesIO()
        img.save(output_buffer, format=output_format)
        return output_buffer.getvalue()


def get_sample_metadata_structure(file_path: str) -> Dict:
    """
    Get a sample of the metadata structure for documentation/debugging.
    
    Args:
        file_path: Path to metadata file (CSV or Excel).
        
    Returns:
        Dictionary with column info and sample values.
    """
    path = Path(file_path)
    file_ext = path.suffix.lower()
    
    if file_ext in ['.xlsx', '.xls']:
        df = pd.read_excel(path, engine='openpyxl', nrows=5)
        df_full = pd.read_excel(path, engine='openpyxl')
    elif file_ext == '.csv':
        df = pd.read_csv(path, nrows=5)
        df_full = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")
    
    return {
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "sample_values": df.head(2).to_dict(orient="records"),
        "row_count": len(df_full)
    }
