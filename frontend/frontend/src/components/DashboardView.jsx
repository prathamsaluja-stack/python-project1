import { Pie, Bar, Scatter, Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, BarElement, Tooltip, Legend, CategoryScale, LinearScale, PointElement, LineElement } from 'chart.js';

ChartJS.register(ArcElement, BarElement, Tooltip, Legend, CategoryScale, LinearScale, PointElement, LineElement);

export default function DashboardView({ result, error }) {
  if (error) {
    return (
      <div className="h-full flex items-center justify-center pb-12">
        <div className="max-w-2xl w-full bg-white rounded-2xl shadow-sm border border-red-100 p-8 text-center">
          <h2 className="text-2xl font-semibold text-red-700">Analysis Error</h2>
          <p className="text-gray-600 mt-4">{error}</p>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="h-full flex items-center justify-center pb-12">
        <div className="max-w-2xl w-full bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center">
          <h2 className="text-2xl font-semibold text-gray-800">No data to analyze</h2>
          <p className="text-gray-600 mt-4">Upload and process a dataset first to see feature engineering results.</p>
        </div>
      </div>
    );
  }

  const {
    insights,
    feature_catalog,
    feature_visualizations,
    feature_relationships,
    feature_engineering_summary,
    correlation_charts,
    seaborn_charts
  } = result;

  const hasFeatureData = feature_catalog && feature_visualizations;

  return (
    <div className="space-y-8">
      {/* Header */}
      <section className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl shadow-sm p-8 text-white">
        <h1 className="text-3xl font-bold mb-2">Feature Engineering Portal</h1>
        <p className="text-blue-100">Comprehensive analysis and visualization of engineered features</p>
        {feature_engineering_summary && (
          <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white/10 rounded-lg p-4">
              <div className="text-2xl font-bold">{feature_engineering_summary.original_dataset.columns}</div>
              <div className="text-sm text-blue-100">Original Features</div>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <div className="text-2xl font-bold">{feature_engineering_summary.processed_dataset.columns}</div>
              <div className="text-sm text-blue-100">Total Features</div>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <div className="text-2xl font-bold">{feature_catalog?.feature_counts?.engineered || 0}</div>
              <div className="text-sm text-blue-100">Engineered Features</div>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <div className="text-2xl font-bold">{feature_engineering_summary.processed_dataset.rows}</div>
              <div className="text-sm text-blue-100">Processed Records</div>
            </div>
          </div>
        )}
      </section>

      {/* Advanced Analytical Visuals (Seaborn) */}
      {seaborn_charts && seaborn_charts.length > 0 && (
        <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <div className="flex items-center space-x-2 mb-6">
            <div className="w-2 h-8 bg-blue-600 rounded-full"></div>
            <h2 className="text-2xl font-bold text-gray-800">Advanced Analytical Visuals</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {seaborn_charts.map((chart, index) => (
              <div key={index} className="bg-gray-50 rounded-xl p-4 border border-gray-100 hover:shadow-md transition-shadow">
                <h3 className="text-lg font-semibold text-gray-700 mb-4 px-2">{chart.title}</h3>
                <div className="bg-white rounded-lg overflow-hidden border border-gray-200">
                  <img 
                    src={`/api/processed/${chart.filepath || chart.filename}`} 
                    alt={chart.title}
                    className="w-full h-auto object-contain"
                    loading="lazy"
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Feature Engineering Summary */}
      {feature_engineering_summary && (
        <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Feature Engineering Pipeline</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-medium text-gray-700 mb-3">Transformations Applied</h3>
              <div className="space-y-2">
                {feature_engineering_summary.transformations_applied.map((transformation, index) => (
                  <div key={index} className="flex items-start">
                    <div className="w-2 h-2 bg-green-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                    <p className="text-sm text-gray-600">{transformation}</p>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-700 mb-3">Feature Types Created</h3>
              <div className="space-y-2">
                {feature_engineering_summary.feature_engineering_steps.map((step, index) => (
                  <div key={index} className="flex items-center">
                    <div className="w-3 h-3 bg-blue-500 rounded-full mr-3"></div>
                    <span className="text-sm font-medium text-gray-700">{step}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Feature Type Distribution */}
      {hasFeatureData && feature_visualizations.feature_types && (
        <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Feature Type Distribution</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="h-80">
              <Doughnut
                data={{
                  labels: feature_visualizations.feature_types.labels,
                  datasets: [{
                    data: feature_visualizations.feature_types.data,
                    backgroundColor: feature_visualizations.feature_types.colors,
                    borderWidth: 2,
                  }],
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: true,
                  plugins: {
                    legend: {
                      position: 'bottom',
                    }
                  }
                }}
              />
            </div>
            <div className="flex items-center">
              <div className="space-y-4">
                {feature_visualizations.feature_types.labels.map((label, index) => (
                  <div key={label} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div
                        className="w-4 h-4 rounded mr-3"
                        style={{ backgroundColor: feature_visualizations.feature_types.colors[index] }}
                      ></div>
                      <span className="font-medium text-gray-700">{label}</span>
                    </div>
                    <span className="text-lg font-bold text-gray-900">
                      {feature_visualizations.feature_types.data[index]}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Feature Quality Dashboard */}
      {hasFeatureData && feature_visualizations.feature_quality && (
        <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Feature Quality Metrics</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {feature_visualizations.feature_quality.map((feature, index) => (
              <div key={index} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-gray-900 truncate" title={feature.feature}>
                    {feature.feature.length > 15 ? `${feature.feature.substring(0, 15)}...` : feature.feature}
                  </h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    feature.type === 'numeric' ? 'bg-blue-100 text-blue-800' :
                    feature.type === 'categorical' ? 'bg-green-100 text-green-800' :
                    'bg-purple-100 text-purple-800'
                  }`}>
                    {feature.type}
                  </span>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Quality Score</span>
                    <span className={`font-bold ${
                      feature.quality_score > 80 ? 'text-green-600' :
                      feature.quality_score > 60 ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      {feature.quality_score}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        feature.quality_score > 80 ? 'bg-green-500' :
                        feature.quality_score > 60 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${feature.quality_score}%` }}
                    ></div>
                  </div>
                  <div className="text-xs text-gray-500">
                    Missing: {feature.missing_percent}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Feature Distributions */}
      {hasFeatureData && feature_visualizations.numeric_distributions && feature_visualizations.numeric_distributions.length > 0 && (
        <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Numeric Feature Distributions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {feature_visualizations.numeric_distributions.map((dist, index) => (
              <div key={index} className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-3">{dist.feature}</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Min:</span>
                    <span className="font-mono">{dist.min.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Q1:</span>
                    <span className="font-mono">{dist.q1.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between font-medium">
                    <span className="text-gray-700">Median:</span>
                    <span className="font-mono">{dist.median.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Q3:</span>
                    <span className="font-mono">{dist.q3.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Max:</span>
                    <span className="font-mono">{dist.max.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Outliers:</span>
                    <span className="font-mono">{dist.outliers}</span>
                  </div>
                  <div className="mt-2">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      dist.distribution_type === 'normal' ? 'bg-green-100 text-green-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {dist.distribution_type.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Categorical Feature Distributions */}
      {hasFeatureData && feature_visualizations.categorical_distributions && feature_visualizations.categorical_distributions.length > 0 && (
        <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Categorical Feature Distributions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {feature_visualizations.categorical_distributions.map((cat, index) => (
              <div key={index} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-medium text-gray-900">{cat.feature}</h3>
                  <span className="text-sm text-gray-500">{cat.cardinality} categories</span>
                </div>
                <div className="space-y-2">
                  {cat.categories.slice(0, 5).map((category, catIndex) => (
                    <div key={catIndex} className="flex items-center justify-between">
                      <span className="text-sm text-gray-700 truncate mr-2" title={category}>
                        {category.length > 20 ? `${category.substring(0, 20)}...` : category}
                      </span>
                      <div className="flex items-center">
                        <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                          <div
                            className="bg-blue-500 h-2 rounded-full"
                            style={{
                              width: `${(cat.values[catIndex] / Math.max(...cat.values)) * 100}%`
                            }}
                          ></div>
                        </div>
                        <span className="text-sm font-mono text-gray-600 w-12 text-right">
                          {cat.values[catIndex]}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Feature Relationships */}
      {correlation_charts && correlation_charts.scatters && correlation_charts.scatters.length > 0 && (
        <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Feature Relationships & Correlations</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {correlation_charts.scatters.map((scatter, index) => (
              <div key={`${scatter.x_label}-${scatter.y_label}-${index}`} className="h-80">
                <h3 className="text-md font-medium mb-2">{scatter.x_label} vs {scatter.y_label}</h3>
                <Scatter
                  data={{
                    datasets: [{
                      label: `${scatter.x_label} vs ${scatter.y_label}`,
                      data: scatter.data || [],
                      backgroundColor: '#3b82f6',
                      pointRadius: 3,
                    }],
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                      legend: {
                        display: false
                      }
                    },
                    scales: {
                      x: { title: { display: true, text: scatter.x_label } },
                      y: { title: { display: true, text: scatter.y_label } }
                    }
                  }}
                />
                <div className="mt-2 text-xs text-gray-600">
                  <p><strong>Correlation:</strong> {scatter.correlation?.toFixed(3)}</p>
                  <p className="text-blue-600 font-medium">{scatter.interpretation}</p>
                  <p className="text-orange-600 italic">{scatter.caution}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Feature Clusters */}
      {feature_relationships && feature_relationships.feature_clusters && Object.keys(feature_relationships.feature_clusters).length > 0 && (
        <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Feature Clusters</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Object.entries(feature_relationships.feature_clusters).map(([clusterName, features], index) => (
              <div key={clusterName} className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <h3 className="font-medium text-purple-900 mb-3">Cluster {index + 1}</h3>
                <div className="flex flex-wrap gap-2">
                  {features.map((feature, featIndex) => (
                    <span key={featIndex} className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm">
                      {feature}
                    </span>
                  ))}
                </div>
                <p className="text-xs text-purple-600 mt-2">
                  {features.length} highly correlated features
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Analysis Insights */}
      {insights && insights.length > 0 && (
        <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Analysis Insights</h2>
          <div className="space-y-3">
            {insights.slice(0, 8).map((insight, index) => (
              <div key={index} className="flex items-start">
                <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                <p className="text-sm text-gray-700">{insight}</p>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}