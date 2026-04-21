export default function DatasetView({ result, error }) {
  if (error) {
    return (
      <div className="h-full flex items-center justify-center pb-12">
        <div className="max-w-2xl w-full bg-white rounded-2xl shadow-sm border border-red-100 p-8 text-center">
          <h2 className="text-2xl font-semibold text-red-700">Upload Error</h2>
          <p className="text-gray-600 mt-4">{error}</p>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="h-full flex items-center justify-center pb-12">
        <div className="max-w-2xl w-full bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center">
          <h2 className="text-2xl font-semibold text-gray-800">No dataset uploaded yet</h2>
          <p className="text-gray-600 mt-4">Upload an Excel or CSV file from the Upload tab to see dataset summary and statistics.</p>
        </div>
      </div>
    );
  }

  const { summary, high_missing_columns, missing_report, correlation_matrix, output_files, processed_csv, performance_notes } = result;

  return (
    <div className="space-y-8">
      {performance_notes && performance_notes.length > 0 ? (
        <section className="bg-yellow-50 rounded-2xl shadow-sm border border-yellow-100 p-6">
          <h3 className="text-lg font-semibold text-yellow-800 mb-3">Performance Notes</h3>
          <ul className="list-disc list-inside text-yellow-900 text-sm space-y-1">
            {performance_notes.map((note, index) => (
              <li key={index}>{note}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Dataset Summary</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="rounded-2xl bg-slate-50 p-4">
            <div className="text-sm text-gray-500">Rows × Columns</div>
            <div className="mt-2 text-2xl font-semibold text-slate-800">{summary?.shape?.[0]} × {summary?.shape?.[1]}</div>
          </div>
          <div className="rounded-2xl bg-slate-50 p-4">
            <div className="text-sm text-gray-500">High-missing columns</div>
            <div className="mt-2 text-2xl font-semibold text-slate-800">{high_missing_columns?.length ?? 0}</div>
          </div>
          <div className="rounded-2xl bg-slate-50 p-4">
            <div className="text-sm text-gray-500">Processed CSV</div>
            <div className="mt-2 text-base font-medium text-slate-800 break-all">{processed_csv}</div>
          </div>
        </div>
      </section>

      <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">High Missing Columns</h3>
        {high_missing_columns && high_missing_columns.length > 0 ? (
          <ul className="list-disc list-inside text-gray-700 space-y-1">
            {high_missing_columns.map((col) => (
              <li key={col}>{col}</li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-500">No columns have more than 60% missing values.</p>
        )}
      </section>

      <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">Missing Value Report</h3>
        {missing_report ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-700 border-collapse">
              <thead>
                <tr>
                  <th className="border-b py-2">Column</th>
                  <th className="border-b py-2">Missing Count</th>
                  <th className="border-b py-2">Missing Ratio</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(missing_report).map(([column, row]) => (
                  <tr key={column} className="even:bg-slate-50">
                    <td className="py-2 pr-4">{column}</td>
                    <td className="py-2 pr-4">{row.missing_count}</td>
                    <td className="py-2 pr-4">{row.missing_ratio}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500">Missing value report is unavailable.</p>
        )}
      </section>

      <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">Correlation Preview</h3>
        {correlation_matrix ? (
          <pre className="bg-slate-50 p-4 rounded-lg overflow-x-auto text-xs text-slate-800">{JSON.stringify(correlation_matrix, null, 2)}</pre>
        ) : (
          <p className="text-gray-500">Correlation matrix not available or not enough numeric columns.</p>
        )}
      </section>
    </div>
  );
}
