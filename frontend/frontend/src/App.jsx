import { useState } from 'react';
import Sidebar from './components/Sidebar';
import UploadView from './components/UploadView';
import DatasetView from './components/DatasetView';
import DashboardView from './components/DashboardView';
import TransformView from './components/TransformView';
import ExportView from './components/ExportView';
import PlaceholderView from './components/PlaceholderView';

function App() {
  const [activeTab, setActiveTab] = useState('Upload');
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState(null);

  const renderContent = () => {
    switch (activeTab) {
      case 'Upload':
        return (
          <UploadView
            onUploadComplete={(result) => {
              setUploadResult(result);
              setUploadError(null);
              setActiveTab('Dataset');
            }}
            onUploadError={(errorMessage) => {
              setUploadError(errorMessage);
              setUploadResult(null);
            }}
          />
        );
      case 'Dataset':
        return <DatasetView result={uploadResult} error={uploadError} />;
      case 'Transform':
        return <TransformView result={uploadResult} error={uploadError} />;
      case 'Dashboard':
        return <DashboardView result={uploadResult} error={uploadError} />;
      case 'Export':
        return <ExportView result={uploadResult} error={uploadError} />;
      default:
        return <UploadView />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden font-sans">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="flex-1 flex flex-col h-full overflow-y-auto">
        <header className="px-8 py-6 border-b border-gray-100 bg-white/50 backdrop-blur-sm sticky top-0 z-10">
          <h1 className="text-2xl font-semibold text-gray-800 tracking-tight">{activeTab}</h1>
          <p className="text-sm text-gray-500 mt-1">Feature Engineering Data Portal</p>
        </header>

        <div className="flex-1 p-8">
          {renderContent()}
        </div>
      </main>
    </div>
  );
}

export default App;
