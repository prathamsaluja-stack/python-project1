import importlib.util
import json
import os
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / 'uploads'
PROCESSED_DIR = BASE_DIR / 'processed'
UPLOAD_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

EXTRACTION_SCRIPT = BASE_DIR / 'feature engineering' / 'extraction.py'
if not EXTRACTION_SCRIPT.exists():
    raise FileNotFoundError(f"Extraction script not found: {EXTRACTION_SCRIPT}")

spec = importlib.util.spec_from_file_location('extraction_module', EXTRACTION_SCRIPT)
extraction_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extraction_module)

app = Flask(__name__)
CORS(app)


@app.errorhandler(Exception)
def handle_exception(error):
    if isinstance(error, HTTPException):
        return jsonify({'error': error.description}), error.code
    return jsonify({'error': str(error)}), 500


@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'message': 'Feature engineering backend is running.',
        'upload_endpoint': '/api/upload',
        'supported_methods': ['POST'],
        'note': 'Use the frontend application on its dev server or POST a file to /api/upload.'
    })


def dataframe_to_json(df, max_rows=20):
    if df is None:
        return None
    trimmed = df.head(max_rows)
    return json.loads(trimmed.to_json(orient='index'))


@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Missing file.'}), 400

    upload_file = request.files['file']
    if upload_file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400

    safe_name = upload_file.filename.replace(' ', '_')
    upload_path = UPLOAD_DIR / f"{uuid.uuid4().hex}_{safe_name}"
    upload_file.save(upload_path)

    output_path = PROCESSED_DIR / f"processed_{uuid.uuid4().hex}.csv"
    try:
        result = extraction_module.process_excel_dataset(
            str(upload_path),
            output_path=str(output_path),
            output_dir=str(PROCESSED_DIR),
        )
    except Exception as exc:
        app.logger.exception('Error processing uploaded dataset')
        return jsonify({'error': 'Backend processing failed', 'detail': str(exc)}), 500

    missing_report = result.get('missing_report')
    correlation_matrix = result.get('correlation_matrix')
    cointegration_matrix = result.get('cointegration_matrix')

    response = {
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
        'output_files': result.get('output_files'),
        'processed_csv': str(output_path.name),
    }

    return jsonify(response)


@app.route('/api/processed/<path:filename>', methods=['GET'])
def download_processed(filename):
    return send_from_directory(PROCESSED_DIR, filename, as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
