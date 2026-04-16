import { UploadCloud, Database, Sliders, LayoutDashboard, DownloadCloud } from 'lucide-react';

const tabs = [
  { id: 'Upload', icon: UploadCloud, label: 'Upload Data' },
  { id: 'Dataset', icon: Database, label: 'Dataset' },
  { id: 'Transform', icon: Sliders, label: 'Transform' },
  { id: 'Dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { id: 'Export', icon: DownloadCloud, label: 'Export' },
];

export default function Sidebar({ activeTab, setActiveTab }) {
  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col py-6 shadow-sm z-20">
      <div className="flex items-center gap-3 w-full px-6 mb-10">
        <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center flex-shrink-0">
          <Database className="w-5 h-5 text-white" />
        </div>
        <span className="font-bold text-xl text-slate-800 tracking-tight">DataPortal</span>
      </div>

      <nav className="w-full px-4 flex flex-col gap-1.5">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 outline-none w-full text-left ${
                isActive 
                  ? 'bg-blue-50 text-blue-700 font-medium shadow-sm' 
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`}
            >
              <Icon className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-blue-600' : 'text-gray-400'}`} />
              <span className="truncate">{tab.label}</span>
            </button>
          );
        })}
      </nav>
      
      <div className="mt-auto px-6 py-4 border-t border-gray-100">
        <p className="text-xs text-gray-400">Feature Engineering v1.0</p>
      </div>
    </aside>
  );
}
