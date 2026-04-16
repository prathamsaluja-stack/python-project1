import { useState } from 'react';
import { FileSpreadsheet, UploadCloud } from 'lucide-react';

export default function UploadView() {
  const [isDragging, setIsDragging] = useState(false);
  const [fileName, setFileName] = useState(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFileName(e.dataTransfer.files[0].name);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFileName(e.target.files[0].name);
    }
  };

  return (
    <div className="h-full flex items-center justify-center pb-12">
      <div className="w-full max-w-2xl bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden transition-all duration-300 hover:shadow-md">
        <div className="p-8 md:p-10 text-center">
          <div className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-800">Upload Dataset</h2>
            <p className="text-gray-500 mt-2 text-sm leading-relaxed max-w-lg mx-auto">
              Upload your raw Excel or CSV files to begin the feature engineering pipeline.
            </p>
          </div>
          
          <div 
            className={`mt-4 relative border-2 border-dashed rounded-xl p-12 transition-all duration-200 group ${
              isDragging 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-200 hover:border-blue-400 hover:bg-slate-50'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <input 
              type="file" 
              id="file-upload" 
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
              onChange={handleFileChange}
              accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
            />
            
            <div className="flex flex-col items-center justify-center gap-4 pointer-events-none">
              <div className={`p-4 rounded-full transition-colors duration-200 ${
                isDragging ? 'bg-blue-100 text-blue-600' : 'bg-gray-50 text-gray-400 group-hover:bg-blue-50 group-hover:text-blue-500'
              }`}>
                {fileName ? <FileSpreadsheet className="w-8 h-8 text-emerald-500" /> : <UploadCloud className="w-8 h-8" />}
              </div>
              <div>
                {fileName ? (
                  <p className="text-lg font-medium text-gray-800">{fileName}</p>
                ) : (
                  <>
                    <p className="text-base font-medium text-gray-700">
                      <span className="text-blue-600">Click to upload</span> or drag and drop
                    </p>
                    <p className="text-sm text-gray-400 mt-1.5">CSV, XLS, or XLSX (max. 50MB)</p>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="mt-8 flex justify-end">
            <button 
              className={`px-6 py-2.5 rounded-lg font-medium transition-all duration-200 ${
                fileName 
                  ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm hover:shadow' 
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'
              }`}
              disabled={!fileName}
            >
              Continue to Dataset
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
