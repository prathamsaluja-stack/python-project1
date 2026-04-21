import { useState } from 'react';

export default function TransformView({ result, error }) {
  const [transformations, setTransformations] = useState([]);

  if (error) {
    return (
      <div className="h-full flex items-center justify-center pb-12">
        <div className="max-w-2xl w-full bg-white rounded-2xl shadow-sm border border-red-100 p-8 text-center">
          <h2 className="text-2xl font-semibold text-red-700">Transform Error</h2>
          <p className="text-gray-600 mt-4">{error}</p>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="h-full flex items-center justify-center pb-12">
        <div className="max-w-2xl w-full bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center">
          <h2 className="text-2xl font-semibold text-gray-800">No data to transform</h2>
          <p className="text-gray-600 mt-4">Upload and process a dataset first to apply transformations.</p>
        </div>
      </div>
    );
  }

  const applyTransformation = (type) => {
    // Placeholder for transformation logic
    setTransformations([...transformations, { type, applied: true }]);
  };

  return (
    <div className="space-y-8">
      <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Data Transformations</h2>
        <p className="text-gray-600 mb-6">Apply common data transformations to prepare your dataset for modeling.</p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <button
            onClick={() => applyTransformation('standardize')}
            className="p-4 border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors"
          >
            <h3 className="font-medium text-gray-800">Standardize</h3>
            <p className="text-sm text-gray-500 mt-1">Scale numeric features to mean 0, std 1</p>
          </button>
          <button
            onClick={() => applyTransformation('normalize')}
            className="p-4 border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors"
          >
            <h3 className="font-medium text-gray-800">Normalize</h3>
            <p className="text-sm text-gray-500 mt-1">Scale to 0-1 range</p>
          </button>
          <button
            onClick={() => applyTransformation('log_transform')}
            className="p-4 border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors"
          >
            <h3 className="font-medium text-gray-800">Log Transform</h3>
            <p className="text-sm text-gray-500 mt-1">Apply log transformation to skewed features</p>
          </button>
          <button
            onClick={() => applyTransformation('one_hot_encode')}
            className="p-4 border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors"
          >
            <h3 className="font-medium text-gray-800">One-Hot Encode</h3>
            <p className="text-sm text-gray-500 mt-1">Convert categorical to binary columns</p>
          </button>
          <button
            onClick={() => applyTransformation('pca')}
            className="p-4 border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors"
          >
            <h3 className="font-medium text-gray-800">PCA</h3>
            <p className="text-sm text-gray-500 mt-1">Principal Component Analysis</p>
          </button>
          <button
            onClick={() => applyTransformation('remove_outliers')}
            className="p-4 border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors"
          >
            <h3 className="font-medium text-gray-800">Remove Outliers</h3>
            <p className="text-sm text-gray-500 mt-1">Filter extreme values</p>
          </button>
        </div>
      </section>

      {transformations.length > 0 && (
        <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Applied Transformations</h3>
          <ul className="list-disc list-inside text-gray-700 space-y-1">
            {transformations.map((t, index) => (
              <li key={index}>{t.type} - Applied</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}