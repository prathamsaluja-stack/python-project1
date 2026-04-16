export default function PlaceholderView({ title, description }) {
  return (
    <div className="h-full flex flex-col pb-12">
      <div className="flex-1 bg-white rounded-2xl shadow-sm border border-gray-100 p-8 flex items-center justify-center text-center">
        <div className="max-w-md">
          <div className="w-16 h-16 bg-slate-50 rounded-2xl flex items-center justify-center mx-auto mb-6 border border-slate-100">
            <svg className="w-8 h-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
          </div>
          <h2 className="text-2xl font-semibold text-gray-800 mb-3">{title}</h2>
          <p className="text-gray-500 leading-relaxed text-sm">
            {description}
          </p>
          <div className="mt-10 pt-8 border-t border-gray-100">
            <span className="inline-flex items-center rounded-md bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-700/10 uppercase tracking-wider">
              Under Construction
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
