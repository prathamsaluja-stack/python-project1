import { DownloadCloud } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export default function ExportView({ result, error }) {
  if (error) {
    return (
      <div className="h-full flex items-center justify-center pb-12">
        <div className="max-w-2xl w-full bg-white rounded-2xl shadow-sm border border-red-100 p-8 text-center">
          <h2 className="text-2xl font-semibold text-red-700">Export Error</h2>
          <p className="text-gray-600 mt-4">{error}</p>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="h-full flex items-center justify-center pb-12">
        <div className="max-w-2xl w-full bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center">
          <h2 className="text-2xl font-semibold text-gray-800">No data to export</h2>
          <p className="text-gray-600 mt-4">Upload and process a dataset first to export results.</p>
        </div>
      </div>
    );
  }

  const { processed_csv, summary, output_files } = result;

  const downloadFile = async (filename) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/processed/${filename}`);
      if (!response.ok) throw new Error('Download failed');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      alert('Download failed: ' + error.message);
    }
  };

  return (
    <div className="space-y-8">
      <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Export Processed Data</h2>
        <p className="text-gray-600 mb-6">Download your feature-engineered dataset and analysis files.</p>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div>
              <h3 className="font-medium text-gray-800">Processed Dataset (CSV)</h3>
              <p className="text-sm text-gray-500">Feature-engineered data with {summary?.shape?.[0]} rows and {summary?.shape?.[1]} columns</p>
            </div>
            <button
              onClick={() => downloadFile(processed_csv)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <DownloadCloud className="w-4 h-4" />
              Download
            </button>
          </div>

          {output_files && Object.entries(output_files).map(([key, path]) => (
            path && (
              <div key={key} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div>
                  <h3 className="font-medium text-gray-800 capitalize">{key.replace('_', ' ')}</h3>
                  <p className="text-sm text-gray-500">Visualization file</p>
                </div>
                <button
                  onClick={() => downloadFile(path)}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  <DownloadCloud className="w-4 h-4" />
                  Download
                </button>
              </div>
            )
          ))}
        </div>
      </section>
    </div>
  );
}