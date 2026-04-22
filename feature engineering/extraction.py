import os
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from statsmodels.tsa.stattools import coint
    HAS_COINTEGRATION = True
except ImportError:
    HAS_COINTEGRATION = False

try:
    import matplotlib
    matplotlib.use('Agg')  
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False

# File loading and dataset inspection

def load_excel_file(path, sheet_name=0):
    """Load a sheet from Excel or a CSV dataset."""
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    if path_obj.suffix.lower() in ['.csv', '.txt']:
        return pd.read_csv(path)
    return pd.read_excel(path, sheet_name=sheet_name)


def summarize_dataframe(df):
    """Return a compact summary of the dataset with standard Python types."""
    return {
        'shape': list(map(int, df.shape)),
        'dtypes': df.dtypes.astype(str).to_dict(),
        'missing_count': {str(k): int(v) for k, v in df.isna().sum().to_dict().items()},
        'missing_ratio': {str(k): float(v) for k, v in (df.isna().mean() * 100).round(2).to_dict().items()},
    }


def missing_value_report(df):
    """Report missing counts and ratios for every column."""
    report = pd.DataFrame({
        'dtype': df.dtypes.astype(str),
        'missing_count': df.isna().sum(),
        'missing_ratio': (df.isna().mean() * 100).round(2),
    })
    return report.sort_values(by='missing_ratio', ascending=False)


def find_high_missing_columns(df, threshold=0.6):
    """Return columns with more than threshold missing values."""
    return df.columns[df.isna().mean() > threshold].tolist()

# Normalization, cleaning, and type inference

def normalize_columns(df):
    """Standardize column names for consistent processing."""
    new_columns = []
    for col in df.columns:
        if isinstance(col, str):
            clean = col.strip().lower()
            clean = clean.replace('/', '_')
            clean = clean.replace('-', '_')
            clean = clean.replace('%', 'pct')
            clean = clean.replace(' ', '_')
            clean = '_'.join(clean.split())
            clean = clean.strip('_')
            new_columns.append(clean)
        else:
            new_columns.append(str(col))
    df.columns = new_columns
    return df

def clean_dataset(df):
    """Clean string values, normalize missing tokens, drop duplicate rows, and filter useless columns."""
    df = df.copy()
    df = df.drop_duplicates()
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].replace({None: np.nan, 'None': np.nan, 'none': np.nan, 'nan': np.nan, '': np.nan})
        mask = df[col].notna()
        df.loc[mask, col] = df.loc[mask, col].astype(str).str.strip()
        df[col] = df[col].replace({'': np.nan, 'nan': np.nan})

    # Drop columns with 100% missing values
    df = df.dropna(axis=1, how='all')
    # Drop columns with only 1 unique value
    cols_to_drop = [c for c in df.columns if df[c].nunique(dropna=True) <= 1]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)

    return df
def infer_column_types(df):
    """Infer datetime and numeric columns from object strings."""
    for col in df.columns:
        if df[col].dtype == object:
            sample = df[col].dropna().astype(str)
            if sample.empty:
                continue
            if sample.str.match(r'^\d{4}-\d{2}-\d{2}').any():
                df[col] = pd.to_datetime(df[col], errors='coerce')
                continue
            if sample.str.match(r'^\d{1,3}(\.\d+)?$').all():
                df[col] = pd.to_numeric(df[col], errors='coerce')
    return df
# Missing value handling

def create_missing_indicators(df, threshold=0.05):
    """Create binary missingness flags for columns with missing values."""
    for col in df.columns:
        missing_ratio = df[col].isna().mean()
        if threshold <= missing_ratio < 1.0:
            df[f'{col}_missing_flag'] = df[col].isna().astype(int)
    return df
def create_row_level_missing_features(df):
    """Generate row-level missing count and ratio features."""
    df['missing_count'] = df.isna().sum(axis=1)
    df['missing_ratio'] = df.isna().mean(axis=1).round(4)
    return df
def impute_numeric_columns(df, numeric_threshold=0.8):
    """Impute numeric values while preserving high-missing columns as explicit indicators."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        missing_ratio = df[col].isna().mean()
        if missing_ratio >= numeric_threshold:
            df[f'{col}_was_missing'] = df[col].isna().astype(int)
        if missing_ratio > 0:
            median = df[col].median(skipna=True)
            fill_value = median if np.isfinite(median) else 0
            df[col] = df[col].fillna(fill_value)
    return df
def impute_categorical_columns(df, high_missing_threshold=0.5):
    """Impute categorical values using mode or explicit missing category."""
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    for col in categorical_cols:
        if df[col].isna().any():
            missing_ratio = df[col].isna().mean()
            if missing_ratio >= high_missing_threshold:
                df[col] = df[col].fillna('missing')
            else:
                mode = df[col].mode(dropna=True)
                fill_value = mode.iloc[0] if not mode.empty else 'missing'
                df[col] = df[col].fillna(fill_value)
    return df

# Separations for numeric, categorical, and datetime columns

def split_dataframe(df):
    """Separate numeric, categorical, and datetime columns."""
    numeric_df = df.select_dtypes(include=[np.number])
    datetime_df = df.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]'])
    categorical_df = df.select_dtypes(include=['object', 'category']).copy()
    return numeric_df, categorical_df, datetime_df


def select_numeric_columns_for_analysis(numeric_df, max_columns=40):
    """Select the most informative numeric columns for correlation and cointegration analysis."""
    if numeric_df.shape[1] <= max_columns:
        return numeric_df
    variances = numeric_df.var(numeric_only=True).sort_values(ascending=False)
    selected = variances.head(max_columns).index.tolist()
    return numeric_df[selected]

# Correlation and cointegration analysis

def compute_numeric_correlations(numeric_df, method='pearson', max_columns=40):
    """Compute a correlation matrix for numeric columns, limited for wide datasets."""
    numeric_df = select_numeric_columns_for_analysis(numeric_df, max_columns=max_columns)
    if numeric_df.shape[1] < 2:
        return pd.DataFrame()
    return numeric_df.corr(method=method)


def compute_cointegration_matrix(numeric_df, significance_level=0.05, max_columns=10):
    """Compute pairwise cointegration p-values for a limited number of numeric columns."""
    if not HAS_COINTEGRATION:
        warnings.warn('statsmodels not installed; cointegration analysis is disabled.')
        return None

    numeric_df = numeric_df.dropna(axis=1, how='all')
    if numeric_df.shape[1] > max_columns:
        numeric_df = select_numeric_columns_for_analysis(numeric_df, max_columns=max_columns)
        warnings.warn(
            f'Cointegration analysis limited to top {max_columns} numeric columns by variance because dataset is wide.'
        )

    columns = numeric_df.columns.tolist()
    if len(columns) < 2:
        return pd.DataFrame()

    matrix = pd.DataFrame(index=columns, columns=columns, dtype=float)

    for i, left in enumerate(columns):
        for right in columns[i + 1 :]:
            try:
                series_left = numeric_df[left].dropna()
                series_right = numeric_df[right].dropna()
                common = series_left.index.intersection(series_right.index)
                if len(common) < 30:
                    matrix.loc[left, right] = np.nan
                    matrix.loc[right, left] = np.nan
                    continue
                _, pvalue, _ = coint(series_left.loc[common], series_right.loc[common])
                matrix.loc[left, right] = pvalue
                matrix.loc[right, left] = pvalue
            except Exception:
                matrix.loc[left, right] = np.nan
                matrix.loc[right, left] = np.nan

    for i in range(len(columns)):
        matrix.iat[i, i] = 0.0
    return matrix

# Descriptive statistics and feature extraction

def describe_numeric_columns(numeric_df):
    """Create a numeric feature summary with basic statistics using standard Python types."""
    if numeric_df.shape[1] == 0:
        return {}
    res = numeric_df.describe().round(4).to_dict()
    # Deep convert to standard types
    return {str(col): {str(k): float(v) if pd.notna(v) else None for k, v in stats.items()} for col, stats in res.items()}


def summarize_categorical_columns(categorical_df, top_n=5):
    """Summarize categorical fields using standard Python types."""
    summary = {}
    for col in categorical_df.columns:
        counts = categorical_df[col].value_counts(dropna=False).head(top_n)
        summary[col] = {str(k): int(v) for k, v in counts.to_dict().items()}
    return summary


def create_statistical_features(df):
    """Generate row-level aggregate statistical features from numeric data."""
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] == 0:
        return df

    df['numeric_mean'] = numeric_df.mean(axis=1)
    df['numeric_std'] = numeric_df.std(axis=1).fillna(0)
    df['numeric_sum'] = numeric_df.sum(axis=1)
    df['numeric_range'] = numeric_df.max(axis=1) - numeric_df.min(axis=1)
    df['numeric_nonzero_count'] = (numeric_df != 0).sum(axis=1)
    df['numeric_positive_count'] = (numeric_df > 0).sum(axis=1)

    for col in numeric_df.columns:
        col_mean = numeric_df[col].mean()
        col_std = numeric_df[col].std()
        if col_std > 0:
            df[f'{col}_zscore'] = (df[col] - col_mean) / col_std
    return df


def extract_text_features(df):
    """Generate simple string statistics for text columns."""
    object_cols = df.select_dtypes(include=['object']).columns
    text_features = []
    for col in object_cols:
        series = df[col].astype(str).fillna('')
        text_features.append(pd.DataFrame({
            f'{col}_length': series.map(len),
            f'{col}_word_count': series.map(lambda x: len(x.split())),
        }))

    if text_features:
        df = pd.concat([df] + text_features, axis=1)
    return df


def generate_feature_catalog(numeric_df, categorical_df, datetime_df, df):
    """Generate a comprehensive feature catalog with metadata and statistics."""
    features = []

    # Numeric features
    for col in numeric_df.columns:
        data = numeric_df[col].dropna()
        if len(data) > 0:
            features.append({
                'name': col,
                'type': 'numeric',
                'dtype': str(numeric_df[col].dtype),
                'missing_percent': (numeric_df[col].isna().mean() * 100).round(2),
                'unique_values': numeric_df[col].nunique(),
                'mean': float(data.mean()),
                'std': float(data.std()),
                'min': float(data.min()),
                'max': float(data.max()),
                'skewness': float(data.skew()),
                'kurtosis': float(data.kurtosis()),
                'distribution_type': 'normal' if abs(data.skew()) < 0.5 else ('right_skewed' if data.skew() > 0 else 'left_skewed'),
                'sample_size': len(data)
            })

    # Categorical features
    for col in categorical_df.columns:
        value_counts = categorical_df[col].value_counts(dropna=False)
        features.append({
            'name': col,
            'type': 'categorical',
            'dtype': str(categorical_df[col].dtype),
            'missing_percent': float((categorical_df[col].isna().mean() * 100).round(2)),
            'unique_values': int(categorical_df[col].nunique()),
            'top_category': str(value_counts.index[0]),
            'top_category_percent': float((value_counts.iloc[0] / len(categorical_df) * 100).round(2)),
            'categories': {str(k): int(v) for k, v in value_counts.head(10).to_dict().items()},
            'cardinality': int(len(value_counts)),
            'sample_size': int(len(categorical_df))
        })

    # Datetime features
    for col in datetime_df.columns:
        dt_data = datetime_df[col].dropna()
        if len(dt_data) > 0:
            features.append({
                'name': col,
                'type': 'datetime',
                'dtype': str(datetime_df[col].dtype),
                'missing_percent': float((datetime_df[col].isna().mean() * 100).round(2)),
                'unique_values': int(datetime_df[col].nunique()),
                'date_range': f"{dt_data.min().date()} to {dt_data.max().date()}",
                'year_range': f"{int(dt_data.dt.year.min())} to {int(dt_data.dt.year.max())}",
                'sample_size': int(len(dt_data))
            })

    # Engineered features (look for patterns that indicate feature engineering)
    engineered_features = []
    all_cols = df.columns.tolist()

    # Missing value indicators
    missing_indicators = [col for col in all_cols if col.endswith('_missing_flag') or col.endswith('_was_missing')]
    engineered_features.extend(missing_indicators)

    # Statistical features
    stat_features = [col for col in all_cols if any(suffix in col for suffix in ['_mean', '_std', '_sum', '_range', '_count', '_zscore'])]
    engineered_features.extend(stat_features)

    # Text features
    text_features = [col for col in all_cols if any(suffix in col for suffix in ['_length', '_word_count'])]
    engineered_features.extend(text_features)

    # Datetime features
    dt_features = [col for col in all_cols if any(suffix in col for suffix in ['_year', '_month', '_day', '_weekday', '_is_null'])]
    engineered_features.extend(dt_features)

    return {
        'all_features': features,
        'engineered_features': list(set(engineered_features)),
        'feature_counts': {
            'numeric': len([f for f in features if f['type'] == 'numeric']),
            'categorical': len([f for f in features if f['type'] == 'categorical']),
            'datetime': len([f for f in features if f['type'] == 'datetime']),
            'engineered': len(set(engineered_features))
        }
    }


def generate_feature_visualizations(numeric_df, categorical_df, feature_catalog):
    """Generate comprehensive feature visualizations."""
    visualizations = {}

    # 1. Feature Type Distribution (Pie Chart)
    feature_types = feature_catalog['feature_counts']
    visualizations['feature_types'] = {
        'labels': ['Numeric', 'Categorical', 'Datetime', 'Engineered'],
        'data': [feature_types['numeric'], feature_types['categorical'], feature_types['datetime'], feature_types['engineered']],
        'colors': ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6']
    }

    # 2. Feature Quality Metrics
    quality_data = []
    for feature in feature_catalog['all_features'][:10]:  # Top 10 features
        quality_score = max(0, 100 - feature['missing_percent'])  # Simple quality score
        quality_data.append({
            'feature': feature['name'],
            'quality_score': quality_score,
            'missing_percent': feature['missing_percent'],
            'type': feature['type']
        })
    visualizations['feature_quality'] = quality_data

    # 3. Numeric Feature Distributions (Box plots data)
    numeric_distributions = []
    for feature in [f for f in feature_catalog['all_features'] if f['type'] == 'numeric'][:6]:
        col = feature['name']
        if col in numeric_df.columns:
            data = numeric_df[col].dropna()
            if len(data) > 10:
                q1, median, q3 = data.quantile([0.25, 0.5, 0.75])
                iqr = q3 - q1
                lower_whisker = max(data.min(), q1 - 1.5 * iqr)
                upper_whisker = min(data.max(), q3 + 1.5 * iqr)
                outliers = len(data[(data < lower_whisker) | (data > upper_whisker)])

                numeric_distributions.append({
                    'feature': col,
                    'min': float(data.min()),
                    'q1': float(q1),
                    'median': float(median),
                    'q3': float(q3),
                    'max': float(data.max()),
                    'outliers': outliers,
                    'distribution_type': feature['distribution_type']
                })
    visualizations['numeric_distributions'] = numeric_distributions

    # 4. Categorical Feature Distributions
    categorical_distributions = []
    for feature in [f for f in feature_catalog['all_features'] if f['type'] == 'categorical'][:6]:
        col = feature['name']
        if col in categorical_df.columns:
            top_categories = list(feature['categories'].keys())[:8]
            top_values = list(feature['categories'].values())[:8]

            categorical_distributions.append({
                'feature': col,
                'categories': top_categories,
                'values': top_values,
                'cardinality': feature['cardinality']
            })
    visualizations['categorical_distributions'] = categorical_distributions

    # 5. Feature Engineering Impact
    engineering_impact = {
        'original_features': feature_catalog['feature_counts']['numeric'] + feature_catalog['feature_counts']['categorical'] + feature_catalog['feature_counts']['datetime'],
        'engineered_features': feature_catalog['feature_counts']['engineered'],
        'total_features': sum(feature_catalog['feature_counts'].values()),
        'engineering_ratio': feature_catalog['feature_counts']['engineered'] / max(1, feature_catalog['feature_counts']['numeric'] + feature_catalog['feature_counts']['categorical'] + feature_catalog['feature_counts']['datetime'])
    }
    visualizations['engineering_impact'] = engineering_impact

    return visualizations


def generate_meaningful_correlation_insights(corr_matrix, correlation_pairs, df, max_pairs=4, max_points=150):
    """Generate intelligent insights and scatterplot data for top correlated pairs."""
    charts = {'scatters': []}
    if not correlation_pairs:
        return charts
        
    for pair in correlation_pairs[:max_pairs]:
        left = pair['left']
        right = pair['right']
        corr = pair['correlation']
        
        if left not in df.columns or right not in df.columns:
            continue
            
        # Extract data without NaNs, limit to max_points for performance
        sub_df = df[[left, right]].dropna().head(max_points)
        if sub_df.empty:
            continue
            
        data = [{'x': float(row[left]), 'y': float(row[right])} for _, row in sub_df.iterrows()]
        
        strength = "Strong" if abs(corr) > 0.7 else ("Moderate" if abs(corr) > 0.4 else "Weak")
        direction = "positive" if corr > 0 else "negative"
        
        interpretation = f"{strength} {direction} relationship. As {left} increases, {right} tends to {'increase' if corr > 0 else 'decrease'}."
        caution = "Correlation does not imply causation. Consider confounding variables."
        
        charts['scatters'].append({
            'x_label': left,
            'y_label': right,
            'data': data,
            'correlation': corr,
            'interpretation': interpretation,
            'caution': caution
        })
        
    return charts


def generate_feature_relationships(corr_matrix, correlation_pairs, cointegration_matrix):
    """Generate feature relationship visualizations."""
    relationships = {}

    # Correlation Heatmap (top 10x10)
    if not corr_matrix.empty:
        top_cols = corr_matrix.columns[:10]
        heatmap_data = corr_matrix.loc[top_cols, top_cols]
        relationships['correlation_heatmap'] = {
            'labels': top_cols.tolist(),
            'data': heatmap_data.values.tolist()
        }

    # Feature Clusters (highly correlated groups)
    if correlation_pairs:
        clusters = {}
        for pair in correlation_pairs:
            if abs(pair['correlation']) > 0.7:
                # Simple clustering by correlation strength
                cluster_key = f"cluster_{len(clusters)}"
                if cluster_key not in clusters:
                    clusters[cluster_key] = []
                clusters[cluster_key].extend([pair['left'], pair['right']])

        # Remove duplicates and keep meaningful clusters
        meaningful_clusters = {}
        for cluster_name, features in clusters.items():
            unique_features = list(set(features))
            if len(unique_features) >= 3:  # Only clusters with 3+ features
                meaningful_clusters[cluster_name] = unique_features

        relationships['feature_clusters'] = meaningful_clusters

    # Cointegration Network
    if cointegration_matrix is not None and not cointegration_matrix.empty:
        cointegration_pairs = []
        cols = cointegration_matrix.columns.tolist()
        for i, left in enumerate(cols):
            for right in cols[i + 1:]:
                pvalue = cointegration_matrix.loc[left, right]
                if pd.notna(pvalue) and pvalue < 0.05:
                    cointegration_pairs.append({
                        'source': left,
                        'target': right,
                        'pvalue': float(pvalue)
                    })
        relationships['cointegration_network'] = cointegration_pairs

    return relationships


def generate_feature_engineering_summary(df, original_shape, feature_catalog):
    """Generate a summary of the feature engineering process with clean types."""
    summary = {
        'original_dataset': {
            'rows': int(original_shape['shape'][0]),
            'columns': int(original_shape['shape'][1])
        },
        'processed_dataset': {
            'rows': int(df.shape[0]),
            'columns': int(df.shape[1])
        },
        'feature_engineering_steps': [],
        'transformations_applied': []
    }

    # Detect transformations
    if any(col.endswith('_missing_flag') for col in df.columns):
        summary['feature_engineering_steps'].append('Missing Value Indicators')
        summary['transformations_applied'].append('Created binary flags for missing values in columns with >5% missing data')

    if any(col.endswith('_was_missing') for col in df.columns):
        summary['feature_engineering_steps'].append('Missing Value Imputation')
        summary['transformations_applied'].append('Imputed missing values in high-missing columns while preserving missing indicators')

    if any('_mean' in col or '_std' in col for col in df.columns):
        summary['feature_engineering_steps'].append('Statistical Features')
        summary['transformations_applied'].append('Generated row-level statistical aggregations (mean, std, range, etc.)')

    if any('_length' in col or '_word_count' in col for col in df.columns):
        summary['feature_engineering_steps'].append('Text Features')
        summary['transformations_applied'].append('Extracted text statistics from string columns')

    if any('_year' in col or '_month' in col for col in df.columns):
        summary['feature_engineering_steps'].append('Datetime Features')
        summary['transformations_applied'].append('Decomposed datetime columns into year, month, day, weekday components')

    if any('_zscore' in col for col in df.columns):
        summary['feature_engineering_steps'].append('Standardization')
        summary['transformations_applied'].append('Created z-score normalized versions of numeric features')

    summary['feature_catalog'] = feature_catalog

    return summary


def encode_categorical_columns(df, max_one_hot=20):
    """Encode categorical features using one-hot or label encoding depending on cardinality."""
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    for col in categorical_cols:
        unique_count = df[col].nunique(dropna=False)
        if unique_count == 2:
            df[col] = df[col].astype('category').cat.codes
        elif unique_count <= max_one_hot:
            dummies = pd.get_dummies(df[col], prefix=col, dummy_na=False, drop_first=False)
            df = pd.concat([df.drop(columns=[col]), dummies], axis=1)
        else:
            df[col] = df[col].astype('category').cat.codes
    return df


def generate_datetime_features(df):
    """Generate year/month/day features from datetime columns."""
    datetime_cols = df.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]']).columns
    for col in datetime_cols:
        df[f'{col}_year'] = df[col].dt.year
        df[f'{col}_month'] = df[col].dt.month
        df[f'{col}_day'] = df[col].dt.day
        df[f'{col}_weekday'] = df[col].dt.weekday
        df[f'{col}_is_null'] = df[col].isna().astype(int)
    return df


def get_top_correlation_pairs(corr_matrix, threshold=0.7, max_pairs=10):
    """Return the top correlated numeric column pairs above threshold."""
    if corr_matrix.empty:
        return []
    pairs = []
    cols = corr_matrix.columns.tolist()
    for i, left in enumerate(cols):
        for right in cols[i + 1 :]:
            value = corr_matrix.loc[left, right]
            if pd.notna(value) and abs(value) >= threshold:
                pairs.append({'left': left, 'right': right, 'correlation': round(float(value), 4)})
    pairs.sort(key=lambda x: abs(x['correlation']), reverse=True)
    return pairs[:max_pairs]


def generate_advanced_seaborn_charts(df, numeric_df, categorical_df, datetime_df, output_dir):
    """
    Implementation of the 8-step Seaborn Feature Engineering Pipeline.
    Generates and saves static PNG charts for various analytical steps.
    """
    if not HAS_PLOTTING:
        return []

    import uuid
    charts = []
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)

    # Step 8: Styling
    sns.set_theme(style="whitegrid")
    
    # Helper to save plot and track
    def save_plot(title, filename_prefix):
        plt.tight_layout()
        plt.title(title, pad=20)
        filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.png"
        full_path = output_path / filename
        plt.savefig(full_path, bbox_inches='tight', dpi=100)
        plt.close()
        charts.append({"title": title, "filename": f"seaborn_plots/{filename}", "filepath": f"seaborn_plots/{filename}"})

    # Step 2: Correlation Plots
    if not numeric_df.empty:
        # Correlation Matrix Calculation
        corr = numeric_df.corr()
        if not corr.empty:
            plt.figure(figsize=(10, 8))
            sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
            save_plot("Numerical Correlation Heatmap", "corr_heatmap")

            # Selection (0.3 < |corr| < 0.85)
            cols = corr.columns.tolist()
            pairs_count = 0
            for i, c1 in enumerate(cols):
                for c2 in cols[i+1:]:
                    val = corr.loc[c1, c2]
                    if 0.3 < abs(val) < 0.85:
                        plt.figure(figsize=(8, 6))
                        sns.scatterplot(data=df, x=c1, y=c2, alpha=0.6)
                        sns.regplot(data=df, x=c1, y=c2, scatter=False, color='red')
                        save_plot(f"Correlation: {c1} vs {c2} (r={val:.2f})", "scatter_reg")
                        pairs_count += 1
                        if pairs_count >= 3: break # Limit clutter
                if pairs_count >= 3: break

    # Step 3: Numerical Distributions
    num_cols = numeric_df.columns.tolist()[:5] # Limit clutter
    for col in num_cols:
        plt.figure(figsize=(10, 4))
        plt.subplot(1, 2, 1)
        sns.histplot(df[col], kde=True, color='skyblue')
        plt.title(f"Histogram: {col}")
        
        plt.subplot(1, 2, 2)
        sns.boxplot(x=df[col], color='lightcoral')
        plt.title(f"Boxplot: {col}")
        save_plot(f"Distribution of {col}", f"dist_{col}")

    # Step 4: Categorical Analysis
    cat_cols = categorical_df.columns.tolist()[:3] # Limit clutter
    for col in cat_cols:
        counts = df[col].value_counts()
        if counts.empty: continue
        unique_count = len(counts)
        plt.figure(figsize=(8, 6))
        if unique_count <= 6:
            plt.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=140, colors=sns.color_palette("pastel"))
            save_plot(f"Category Pie Chart: {col}", f"pie_{col}")
        else:
            top_counts = counts.head(10)
            sns.countplot(data=df, x=col, order=top_counts.index, palette="viridis")
            plt.xticks(rotation=45)
            save_plot(f"Category Bar Chart (Top 10): {col}", f"bar_{col}")

    # Step 5: Categorical vs Numerical
    if not numeric_df.empty and not categorical_df.empty:
        # Cross join top pairs
        c1 = categorical_df.columns[0]
        n1 = numeric_df.columns[0]
        plt.figure(figsize=(10, 6))
        means = df.groupby(c1)[n1].mean().sort_values(ascending=False).head(10)
        sns.barplot(x=means.index, y=means.values, palette="magma")
        plt.title(f"Mean {n1} by {c1}")
        plt.xticks(rotation=45)
        save_plot(f"Categorical Mean: {n1} by {c1}", "cat_vs_num")

    # Step 6: Time Series Analysis
    if not datetime_df.empty and not numeric_df.empty:
        t_col = datetime_df.columns[0]
        n_col = numeric_df.columns[0]
        temp_df = df[[t_col, n_col]].dropna().sort_values(by=t_col)
        if not temp_df.empty:
            plt.figure(figsize=(12, 6))
            sns.lineplot(data=temp_df, x=t_col, y=n_col, marker='o', alpha=0.5)
            if len(temp_df) > 7:
                temp_df['rolling'] = temp_df[n_col].rolling(window=min(7, len(temp_df))).mean()
                sns.lineplot(data=temp_df, x=t_col, y='rolling', color='red', label='7-Day Rolling Avg')
            plt.xticks(rotation=45)
            save_plot(f"Time Series: {n_col} over {t_col}", "timeseries")

    # Step 7: Missing Data Visualization
    missing_pct = (df.isna().mean() * 100).sort_values(ascending=False)
    if missing_pct.any():
        plt.figure(figsize=(12, 6))
        top_missing = missing_pct.head(15)
        sns.barplot(x=top_missing.index, y=top_missing.values, palette="Reds_r")
        plt.ylabel("Missing Percentage (%)")
        plt.title("Missing Data Per Column")
        plt.xticks(rotation=45)
        save_plot("Missing Data Overview", "missing_bar")

    return charts


def build_performance_notes(numeric_df, has_tokenize_statsmodels=False, plot_available=True):
    notes = []
    if numeric_df.shape[1] > 40:
        notes.append('Correlation analysis was limited to the top 40 numeric columns by variance to preserve performance for wide datasets.')
    if has_tokenize_statsmodels and numeric_df.shape[1] > 10:
        notes.append('Cointegration analysis was limited to the top 10 numeric columns by variance to preserve runtime performance.')
    if not plot_available:
        notes.append('Plotting is disabled because matplotlib/seaborn are not installed; visual reports will not be generated.')
    return notes


def build_insights(
    summary,
    high_missing_cols,
    top_corr_pairs,
    cointegration_matrix,
    numeric_df,
    categorical_df,
    datetime_df,
):
    """Build human-readable insights from analysis results."""
    insights = []
    rows, cols = summary['shape']
    insights.append(f"Dataset has {rows} rows and {cols} columns.")
    insights.append(
        f"Detected {numeric_df.shape[1]} numeric features, {categorical_df.shape[1]} categorical features, and {datetime_df.shape[1]} datetime features."
    )
    if high_missing_cols:
        insights.append(
            f"Columns with >60% missing values: {', '.join(high_missing_cols)}. These may still contain important signals, so they were preserved and flagged."
        )
    else:
        insights.append("No columns have more than 60% missing values.")

    if top_corr_pairs:
        pairs_text = ", ".join([f"{p['left']}↔{p['right']} ({p['correlation']})" for p in top_corr_pairs[:5]])
        insights.append(f"Strong numeric correlations found: {pairs_text}.")
    else:
        insights.append("No strongly correlated numeric feature pairs were identified above the threshold.")

    if cointegration_matrix is not None:
        low_p_pairs = []
        cols = cointegration_matrix.columns.tolist()
        for i, left in enumerate(cols):
            for right in cols[i + 1 :]:
                pvalue = cointegration_matrix.loc[left, right]
                if pd.notna(pvalue) and pvalue < 0.05:
                    low_p_pairs.append({'left': left, 'right': right, 'pvalue': round(float(pvalue), 4)})
        if low_p_pairs:
            pair_text = ", ".join([f"{p['left']}↔{p['right']} (p={p['pvalue']})" for p in low_p_pairs[:5]])
            insights.append(f"Cointegration evidence found for: {pair_text}.")
        else:
            insights.append("Cointegration analysis did not find strong evidence of paired series behavior.")
    else:
        insights.append("Cointegration analysis was not performed because statsmodels is not installed.")

    return insights

# Optional visualizations for frontend or reports

def visualize_missingness(df, output_dir=None, max_columns=120, max_rows=5000):
    """Save a missingness heatmap if plotting is available."""
    if not HAS_PLOTTING:
        return None
    if df.shape[1] > max_columns or df.shape[0] > max_rows:
        warnings.warn('Skipping missingness heatmap for large dataset to preserve performance.')
        return None
    missing = df.isna()
    plt.figure(figsize=(12, 6))
    sns.heatmap(missing.T, cbar=False, cmap='viridis')
    plt.title('Missingness heatmap')
    if output_dir:
        path = os.path.join(output_dir, 'missingness_heatmap.png')
        plt.savefig(path, bbox_inches='tight')
        plt.close()
        return path
    plt.close()
    return None


def visualize_correlation(df, output_dir=None, method='pearson', max_columns=40):
    """Save a correlation matrix plot for numeric data."""
    if not HAS_PLOTTING:
        return None
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] > max_columns:
        warnings.warn('Skipping correlation plot for wide dataset to preserve performance.')
        return None
    corr = compute_numeric_correlations(numeric_df, method=method)
    if corr.empty:
        return None
    plt.figure(figsize=(12, 10))
    sns.heatmap(corr, annot=False, cmap='coolwarm', center=0)
    plt.title(f'Numeric correlation ({method})')
    if output_dir:
        path = os.path.join(output_dir, 'correlation_matrix.png')
        plt.savefig(path, bbox_inches='tight')
        plt.close()
        return path
    plt.close()
    return None
# Orchestration for extraction and feature engineering

def process_excel_dataset(
    path,
    output_path=None,
    sheet_name=0,
    missing_indicator_threshold=0.05,
    high_missing_threshold=0.6,
    output_dir=None,
):
    df = load_excel_file(path, sheet_name=sheet_name)
    df = normalize_columns(df)
    df = clean_dataset(df)
    df = infer_column_types(df)

    missing_report = missing_value_report(df)
    high_missing_cols = find_high_missing_columns(df, threshold=high_missing_threshold)

    df = create_missing_indicators(df, threshold=missing_indicator_threshold)
    df = create_row_level_missing_features(df)
    df = impute_numeric_columns(df)
    df = impute_categorical_columns(df)
    df = generate_datetime_features(df)
    df = create_statistical_features(df)
    df = extract_text_features(df)

    numeric_df, categorical_df, datetime_df = split_dataframe(df)
    
    # Ensure some numeric data for charts if possible
    if numeric_df.empty and not df.empty:
        df = infer_column_types(df)
        numeric_df, categorical_df, datetime_df = split_dataframe(df)

    if numeric_df.empty:
        numeric_summary = {}
        corr_matrix = pd.DataFrame()
        correlation_pairs = []
        cointegration_matrix = pd.DataFrame()
    else:
        selected_numeric = select_numeric_columns_for_analysis(numeric_df)
        numeric_summary = describe_numeric_columns(numeric_df)
        corr_matrix = compute_numeric_correlations(selected_numeric)
        correlation_pairs = get_top_correlation_pairs(corr_matrix)
        cointegration_matrix = compute_cointegration_matrix(selected_numeric) if HAS_COINTEGRATION else None

    categorical_summary = summarize_categorical_columns(categorical_df)
    insights = build_insights(
        summarize_dataframe(df),
        high_missing_cols,
        correlation_pairs,
        cointegration_matrix,
        numeric_df,
        categorical_df,
        datetime_df,
    )

    final_df = encode_categorical_columns(df.copy())

    if output_path:
        final_df.to_csv(output_path, index=False)

    extra_files = {}
    if output_dir and HAS_PLOTTING:
        extra_files['missingness_plot'] = visualize_missingness(final_df, output_dir=output_dir)
        extra_files['correlation_plot'] = visualize_correlation(final_df, output_dir=output_dir)

    performance_notes = build_performance_notes(
        numeric_df,
        has_tokenize_statsmodels=HAS_COINTEGRATION,
        plot_available=HAS_PLOTTING,
    )

    if not HAS_COINTEGRATION:
        performance_notes.append('Statsmodels is not installed, so cointegration analysis was skipped.')

    correlation_charts = generate_meaningful_correlation_insights(corr_matrix, correlation_pairs, df)
    feature_catalog = generate_feature_catalog(numeric_df, categorical_df, datetime_df, df)
    feature_visualizations = generate_feature_visualizations(numeric_df, categorical_df, feature_catalog)
    feature_relationships = generate_feature_relationships(corr_matrix, correlation_pairs, cointegration_matrix)
    feature_engineering_summary = generate_feature_engineering_summary(df, summarize_dataframe(df), feature_catalog)
    
    # Generate Advanced Seaborn Charts (Step 2-8)
    seaborn_charts = []
    if output_dir and HAS_PLOTTING:
        seaborn_charts_dir = Path(output_dir) / "seaborn_plots"
        seaborn_charts = generate_advanced_seaborn_charts(df, numeric_df, categorical_df, datetime_df, str(seaborn_charts_dir))
        # Update extra_files to include these
        for chart in seaborn_charts:
            extra_files[chart['title']] = str(Path(output_dir) / chart['filename'])

    return {
        'processed_dataframe': final_df,
        'missing_report': missing_report,
        'high_missing_columns': high_missing_cols,
        'numeric_dataframe': numeric_df,
        'categorical_dataframe': categorical_df,
        'datetime_dataframe': datetime_df,
        'correlation_matrix': corr_matrix,
        'correlation_pairs': correlation_pairs,
        'cointegration_matrix': cointegration_matrix,
        'numeric_summary': numeric_summary,
        'categorical_summary': categorical_summary,
        'datetime_columns': list(datetime_df.columns),
        'insights': insights,
        'output_files': extra_files,
        'performance_notes': performance_notes,
        'correlation_charts': correlation_charts,
        'feature_catalog': feature_catalog,
        'feature_visualizations': feature_visualizations,
        'feature_relationships': feature_relationships,
        'feature_engineering_summary': feature_engineering_summary,
        'seaborn_charts': seaborn_charts,
        'summary': summarize_dataframe(final_df),
    }
# CLI entrypoint

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        raise SystemExit('Usage: python extraction.py <excel-file-path> [output-csv-path] [output-dir]')

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) >= 3 else 'processed_output.csv'
    output_dir = sys.argv[3] if len(sys.argv) >= 4 else None

    result = process_excel_dataset(
        input_path,
        output_path=output_path,
        output_dir=output_dir,
    )

    print('Processed shape:', result['summary']['shape'])
    print('Missing columns with any missing values:')
    print(result['missing_report'].head(20).to_string())
    print('High-missing columns (>60% missing):', result['high_missing_columns'])
    print('Numeric correlation matrix sample:')
    if not result['correlation_matrix'].empty:
        print(result['correlation_matrix'].iloc[:5, :5].to_string())
    if result['cointegration_matrix'] is not None:
        print('Cointegration p-value matrix sample:')
        print(result['cointegration_matrix'].iloc[:5, :5].to_string())
    if result['output_files']:
        print('Generated visualization files:', result['output_files'])
