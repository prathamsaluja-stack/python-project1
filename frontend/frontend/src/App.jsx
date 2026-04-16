import { useState } from 'react';
import Sidebar from './components/Sidebar';
import UploadView from './components/UploadView';
import PlaceholderView from './components/PlaceholderView';

function App() {
  const [activeTab, setActiveTab] = useState('Upload');

  const renderContent = () => {
    switch (activeTab) {
      case 'Upload':
        return <UploadView />;
      case 'Dataset':
        return <PlaceholderView title="Dataset Explorer" description="View and filter your uploaded datasets in a tabular format." />;
      case 'Transform':
        return <PlaceholderView title="Data Transformations" description="Apply feature engineering operations like scaling, encoding, and imputation." />;
      case 'Dashboard':
        return <PlaceholderView title="Analysis Dashboard" description="Visualize dataset statistics, correlations, and feature importance." />;
      case 'Export':
        return <PlaceholderView title="Export Data" description="Download the processed dataset or pipeline configurations." />;
      default:
        return <UploadView />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden font-sans">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="flex-1 flex flex-col h-full overflow-y-auto">
        {/* Simple header to provide context, mostly visual spacing */}
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
