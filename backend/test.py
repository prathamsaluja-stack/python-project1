import sys
sys.path.append('../feature engineering')
import importlib.util

spec = importlib.util.spec_from_file_location('extraction_module', '../feature engineering/extraction.py')
ext = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ext)

try:
    ext.process_excel_dataset('test.csv', output_path='test_out.csv')
    print("SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
