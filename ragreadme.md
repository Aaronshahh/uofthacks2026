# Footwear RAG Agent

A forensic footwear analysis system that uses RAG (Retrieval-Augmented Generation) to find similar footprints and provide metadata insights. The system embeds footprint images, stores them in a Snowflake vector database, and returns the top 3 closest matches as separate metadata cases.

## Features

- **Data Ingestion**: Process zip files containing footprint images (.tiff) and Excel/CSV metadata
- **Vector Embeddings**: Generate image embeddings using Snowflake Cortex
- **RAG Query**: Upload a footprint image to find the 3 most similar matches
- **Metadata Cases**: Returns 3 possible cases (CASE A, B, C) with full metadata (no images in output)
- **Modern Web UI**: Responsive frontend for easy querying

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Zip Files     │────▶│    Data      │────▶│   Snowflake     │
│   + CSV         │     │   Processor  │     │  Vector DB      │
└─────────────────┘     └──────────────┘     └────────┬────────┘
                                                      │
                        ┌──────────────┐              │
                        │   FastAPI    │◀─────────────┘
                        │   Backend    │
                        └──────┬───────┘
                               │
┌─────────────────┐            │
│  Query Image    │────────────┤
└─────────────────┘            │
                               ▼
                        ┌──────────────┐
                        │  3 Metadata  │
                        │    Cases     │
                        └──────────────┘
```

## Quick Start

### 1. Install Dependencies

```bash
cd footwear_rag
pip install -r requirements.txt
```

### 2. Configure Snowflake

Copy and edit the configuration file:

```bash
# Edit config/config.yaml with your Snowflake credentials
```

Or set environment variables:

```bash
export SNOWFLAKE_ACCOUNT="your_account"
export SNOWFLAKE_USER="your_username"
export SNOWFLAKE_PASSWORD="your_password"
export SNOWFLAKE_WAREHOUSE="your_warehouse"
export SNOWFLAKE_DATABASE="your_database"
export SNOWFLAKE_SCHEMA="your_schema"
export SNOWFLAKE_ROLE="your_role"
```

### 3. Prepare Data

Place your data in the following directories:

```
footwear_rag/
└── data/
    └── zip_files/          # Put zip files and metadata file here
        ├── part1.zip       # Image datasets (part1.zip - part5.zip)
        ├── part2.zip
        ├── part3.zip
        ├── part4.zip
        ├── part5.zip
        └── Data-information.xlsx  # Metadata Excel file
```

The metadata Excel file should have:
- An `id` column that matches the image filenames (without extension)
- Metadata columns (e.g., `age`, `weight`, `height`, `gender`)

**Note**: The system supports both `.csv` and `.xlsx` files for metadata.

### 4. Ingest Data

Run the ingestion script:

```bash
python footwear_rag/scripts/ingest_data.py
```

Options:
- `--zip-dir PATH`: Custom zip files directory
- `--csv PATH`: Custom CSV file path
- `--drop-existing`: Drop existing data before ingestion
- `--dry-run`: Process without inserting to database
- `--verbose`: Enable verbose logging

### 5. Start the API Server

```bash
cd footwear_rag
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Or use Python:

```bash
python -m footwear_rag.backend.main
```

### 6. Access the Application

- **Web UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## API Endpoints

### POST /api/query

Upload a footprint image and get the 3 closest matches.

**Request**: Multipart form with `image` file

**Response**:
```json
{
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
    "case_b": { ... },
    "case_c": { ... }
  },
  "query_metadata": {
    "timestamp": "2026-01-17T10:30:00",
    "embedding_model": "snowflake_native",
    "results_found": 3,
    "processing_time_ms": 125.5
  }
}
```

### POST /api/ingest

Trigger data ingestion from configured paths.

**Request Body**:
```json
{
  "zip_directory": "path/to/zips",
  "csv_file": "path/to/metadata.xlsx",
  "drop_existing": false
}
```

**Note**: The `csv_file` parameter accepts both `.csv` and `.xlsx` files.

### GET /api/health

Check system health and database status.

## Configuration

Edit `config/config.yaml`:

```yaml
snowflake:
  account: "<your_snowflake_account>"
  user: "<your_username>"
  password: "<your_password>"
  warehouse: "<your_warehouse>"
  database: "<your_database>"
  schema: "<your_schema>"
  role: "<your_role>"

data:
  zip_directory: "footwear_rag/data/zip_files"
  csv_file: "footwear_rag/data/zip_files/Data-information.xlsx"  # Supports .csv or .xlsx
  image_extensions:
    - ".tiff"
    - ".tif"
  id_column: "id"

embedding:
  model: "snowflake_native"
  image_dimension: 1024

api:
  host: "0.0.0.0"
  port: 8000
  cors_origins:
    - "*"
```

## Project Structure

```
uofthacks2026/
├── footwear_rag/
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI application
│   │   ├── config.py          # Configuration management
│   │   ├── database.py        # Snowflake operations
│   │   ├── embeddings.py      # Embedding generation
│   │   ├── data_processor.py  # Zip/Excel/CSV processing
│   │   ├── rag_query.py       # RAG query logic
│   │   ├── models.py          # Pydantic models
│   │   └── routes/
│   │       ├── ingest.py      # Ingestion endpoints
│   │       └── query.py       # Query endpoints
│   ├── frontend/
│   │   ├── index.html
│   │   ├── styles.css
│   │   └── app.js
│   ├── scripts/
│   │   └── ingest_data.py     # Standalone ingestion
│   ├── data/
│   │   └── zip_files/         # Input data
│   └── requirements.txt
├── config/
│   └── config.yaml
└── README.md
```

## Query Flow

1. **Upload**: User uploads a footprint image
2. **Embed**: System generates embedding using Snowflake Cortex
3. **Search**: Vector similarity search finds top 3 matches
4. **Average**: Embeddings are averaged (internal use)
5. **Return**: 3 metadata cases returned (CASE A, B, C)

## Database Schema

```sql
CREATE TABLE footprint_vectors (
    id VARCHAR PRIMARY KEY,
    image_path VARCHAR,
    metadata VARIANT,                              -- JSON metadata
    image_embedding VECTOR(FLOAT, 1024),          -- Image embedding
    created_at TIMESTAMP
);
```

## Development

### Running Tests

```bash
pytest footwear_rag/tests/
```

### Local Embedding Mode

If Snowflake Cortex is unavailable, use local embeddings:

```bash
python footwear_rag/scripts/ingest_data.py --use-local-embeddings
```

Or use the `/api/query/local` endpoint for queries.

## License

MIT License
