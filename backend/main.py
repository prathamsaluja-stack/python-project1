import importlib.util
import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

# Setup paths relative to this file (backend/main.py)
# Root is one level up
BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
UPLOAD_DIR = ROOT_DIR / 'uploads'
PROCESSED_DIR = ROOT_DIR / 'processed'

UPLOAD_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

# Path to extraction script
EXTRACTION_SCRIPT = ROOT_DIR / 'feature engineering' / 'extraction.py'

if not EXTRACTION_SCRIPT.exists():
    # If not found at ROOT_DIR/feature engineering/extraction.py, check if we are in the wrong place
    # Maybe backend is a sibling of feature engineering
    EXTRACTION_SCRIPT = BACKEND_DIR.parent / 'feature engineering' / 'extraction.py'

if not EXTRACTION_SCRIPT.exists():
    raise FileNotFoundError(f"Extraction script not found: {EXTRACTION_SCRIPT}")

# Import extraction module
spec = importlib.util.spec_from_file_location('extraction_module', EXTRACTION_SCRIPT)
extraction_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extraction_module)

app = FastAPI(
    title="Feature Engineering API",
    description="Backend API for the Feature Engineering Data Portal."
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def dataframe_to_json(df, max_rows=20):
    if df is None:
        return None
    trimmed = df.head(max_rows)
    # Convert to JSON using pandas and then parse back to dict to be JSON-serializable
    return json.loads(trimmed.to_json(orient='index'))

@app.get("/")
def read_root():
    return {
        "message": "Feature Engineering API is running.",
        "upload_endpoint": "/api/upload",
        "health": "/health"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        import numpy as np
        import math
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            if np.isnan(obj) or np.isinf(obj):
                return None
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        elif isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
        return json.JSONEncoder.default(self, obj)

def clean_for_json(obj):
    """Recursively convert NaN/Inf and Numpy types to JSON-compliant values."""
    import math
    import numpy as np
    import pandas as pd
    
    if isinstance(obj, dict):
        return {str(k): clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [clean_for_json(x) for x in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, (np.integer, np.floating)):
        if isinstance(obj, np.floating) and (np.isnan(obj) or np.isinf(obj)):
            return None
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return clean_for_json(obj.tolist())
    elif isinstance(obj, (pd.Series, pd.Index)):
        return clean_for_json(obj.to_dict())
    elif hasattr(obj, 'dtype'): # Catch-all for other numpy-like scalars
        try:
            val = obj.item()
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                return None
            return val
        except:
            return str(obj)
    return obj

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing file name.")
    
    # Save the file
    safe_name = file.filename.replace(' ', '_')
    unique_id = uuid.uuid4().hex
    upload_path = UPLOAD_DIR / f"{unique_id}_{safe_name}"
    
    try:
        with open(upload_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    output_path = PROCESSED_DIR / f"processed_{unique_id}.csv"
    
    try:
        # Run extraction logic
        result = extraction_module.process_excel_dataset(
            str(upload_path),
            output_path=str(output_path),
            output_dir=str(PROCESSED_DIR),
        )
    except Exception as exc:
        # Log the error for debugging
        print(f"Error processing dataset: {exc}")
        raise HTTPException(status_code=500, detail=f"Backend processing failed: {str(exc)}")

    # Construct response
    missing_report = result.get('missing_report')
    correlation_matrix = result.get('correlation_matrix')
    cointegration_matrix = result.get('cointegration_matrix')

    response_data = {
        'summary': result.get('summary'),
        'high_missing_columns': result.get('high_missing_columns'),
        'missing_report': dataframe_to_json(missing_report),
        'correlation_matrix': dataframe_to_json(correlation_matrix),
        'correlation_pairs': result.get('correlation_pairs'),
        'cointegration_matrix': dataframe_to_json(cointegration_matrix),
        'numeric_summary': result.get('numeric_summary'),
        'categorical_summary': result.get('categorical_summary'),
        'datetime_columns': result.get('datetime_columns'),
        'insights': result.get('insights'),
        'performance_notes': result.get('performance_notes'),
        'correlation_charts': result.get('correlation_charts'),
        'feature_catalog': result.get('feature_catalog'),
        'feature_visualizations': result.get('feature_visualizations'),
        'feature_relationships': result.get('feature_relationships'),
        'feature_engineering_summary': result.get('feature_engineering_summary'),
        'seaborn_charts': result.get('seaborn_charts'),
        'output_files': result.get('output_files'),
        'processed_csv': str(output_path.name),
    }

    # Manual serialization to handle Numpy types and NaNs
    try:
        cleaned_data = clean_for_json(response_data)
        return JSONResponse(content=cleaned_data)
    except Exception as e:
        print(f"JSON Encoding Error: {e}")
        raise HTTPException(status_code=500, detail=f"Data serialization error: {str(e)}")


@app.get("/api/processed/{filepath:path}")
async def download_processed(filepath: str):
    file_path = PROCESSED_DIR / filepath
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    
    # Determine media type
    ext = file_path.suffix.lower()
    media_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.csv': 'text/csv',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }
    mtype = media_types.get(ext, 'application/octet-stream')
    
    return FileResponse(path=file_path, filename=filepath.split('/')[-1], media_type=mtype)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
