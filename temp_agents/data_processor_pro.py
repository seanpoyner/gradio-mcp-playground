import gradio as gr
import pandas as pd
import numpy as np
import json
import io
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')
import os

class DataProcessorAgent:
    def __init__(self):
        self.df = None
        self.analysis_history = []
        
    def load_and_analyze(self, file_content, operation, target_column=""):
        """Advanced data processing with ML capabilities"""
        try:
            if not file_content:
                return "No file uploaded", None, "Upload a CSV or JSON file to begin analysis"
                
            content = file_content.decode('utf-8')
            
            # Parse data
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    self.df = pd.DataFrame(data)
                else:
                    self.df = pd.json_normalize(data)
            except:
                try:
                    self.df = pd.read_csv(io.StringIO(content))
                except Exception as e:
                    return f"Error parsing file: {str(e)}", None, "Please check your file format"
            
            # Perform analysis based on operation
            if operation == "Data Overview":
                overview = self._generate_overview()
                plot = self._create_overview_plot()
                return overview, plot, "Data loaded successfully! Explore other analysis options."
                
            elif operation == "Statistical Summary":
                summary = self._statistical_analysis()
                plot = self._create_correlation_plot()
                return summary, plot, "Statistical analysis complete"
                
            elif operation == "Missing Data Analysis":
                missing_analysis = self._missing_data_analysis()
                plot = self._create_missing_data_plot()
                return missing_analysis, plot, "Missing data analysis complete"
                
            elif operation == "Clustering Analysis":
                cluster_results = self._clustering_analysis()
                plot = self._create_cluster_plot()
                return cluster_results, plot, "Clustering analysis complete"
                
            elif operation == "Trend Analysis":
                trend_results = self._trend_analysis(target_column)
                plot = self._create_trend_plot(target_column)
                return trend_results, plot, "Trend analysis complete"
                
            elif operation == "Export Enhanced":
                export_data = self._export_enhanced()
                return export_data, None, "Data exported with enhancements"
                
        except Exception as e:
            return f"Analysis error: {str(e)}", None, "Please check your data and try again"
    
    def _generate_overview(self):
        """Generate comprehensive data overview"""
        overview = f"📊 **Data Overview**\n\n"
        overview += f"• **Shape**: {self.df.shape[0]} rows × {self.df.shape[1]} columns\n"
        overview += f"• **Memory Usage**: {self.df.memory_usage(deep=True).sum() / 1024:.1f} KB\n\n"
        
        overview += f"**Column Information:**\n"
        for col in self.df.columns:
            dtype = str(self.df[col].dtype)
            null_count = self.df[col].isnull().sum()
            unique_count = self.df[col].nunique()
            overview += f"• {col}: {dtype} ({null_count} nulls, {unique_count} unique)\n"
        
        overview += f"\n**Sample Data:**\n{self.df.head().to_string()}"
        return overview
    
    def _statistical_analysis(self):
        """Enhanced statistical analysis"""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) == 0:
            return "No numeric columns found for statistical analysis"
        
        stats = "📈 **Statistical Summary**\n\n"
        
        desc = self.df[numeric_cols].describe()
        stats += f"**Descriptive Statistics:**\n{desc.to_string()}\n\n"
        
        # Correlation analysis
        if len(numeric_cols) > 1:
            corr_matrix = self.df[numeric_cols].corr()
            strong_corr = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_val = corr_matrix.iloc[i, j]
                    if abs(corr_val) > 0.7:
                        strong_corr.append(f"{corr_matrix.columns[i]} ↔ {corr_matrix.columns[j]}: {corr_val:.3f}")
            
            if strong_corr:
                stats += f"**Strong Correlations (|r| > 0.7):**\n"
                for corr in strong_corr:
                    stats += f"• {corr}\n"
            else:
                stats += "**No strong correlations found**\n"
        
        return stats
    
    def _missing_data_analysis(self):
        """Analyze missing data patterns"""
        missing = self.df.isnull().sum()
        missing_pct = (missing / len(self.df)) * 100
        
        analysis = "🔍 **Missing Data Analysis**\n\n"
        
        if missing.sum() == 0:
            analysis += "✅ No missing data found!"
        else:
            analysis += f"**Missing Data Summary:**\n"
            for col in missing[missing > 0].index:
                analysis += f"• {col}: {missing[col]} ({missing_pct[col]:.1f}%)\n"
            
            # Suggest strategies
            analysis += f"\n**Recommended Actions:**\n"
            high_missing = missing_pct[missing_pct > 50]
            medium_missing = missing_pct[(missing_pct > 10) & (missing_pct <= 50)]
            low_missing = missing_pct[(missing_pct > 0) & (missing_pct <= 10)]
            
            if len(high_missing) > 0:
                analysis += f"• Consider dropping columns with >50% missing: {list(high_missing.index)}\n"
            if len(medium_missing) > 0:
                analysis += f"• Impute or investigate columns with 10-50% missing: {list(medium_missing.index)}\n"
            if len(low_missing) > 0:
                analysis += f"• Simple imputation for columns with <10% missing: {list(low_missing.index)}\n"
        
        return analysis
    
    def _clustering_analysis(self):
        """Perform clustering analysis on numeric data"""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) < 2:
            return "❌ Need at least 2 numeric columns for clustering analysis"
        
        # Prepare data
        X = self.df[numeric_cols].fillna(self.df[numeric_cols].mean())
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Determine optimal clusters using elbow method
        inertias = []
        K_range = range(2, min(11, len(X)))
        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(X_scaled)
            inertias.append(kmeans.inertia_)
        
        # Find elbow point (simple method)
        optimal_k = K_range[0]
        max_diff = 0
        for i in range(1, len(inertias)-1):
            diff = inertias[i-1] - inertias[i+1]
            if diff > max_diff:
                max_diff = diff
                optimal_k = K_range[i]
        
        # Perform clustering with optimal k
        kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)
        
        # Analyze clusters
        cluster_summary = f"🎯 **Clustering Analysis**\n\n"
        cluster_summary += f"• **Optimal Clusters**: {optimal_k}\n"
        cluster_summary += f"• **Inertia**: {kmeans.inertia_:.2f}\n\n"
        
        # Cluster characteristics
        self.df['Cluster'] = clusters
        cluster_summary += f"**Cluster Characteristics:**\n"
        for cluster_id in range(optimal_k):
            cluster_data = self.df[self.df['Cluster'] == cluster_id][numeric_cols]
            cluster_summary += f"\n**Cluster {cluster_id}** ({len(cluster_data)} points):\n"
            for col in numeric_cols[:3]:  # Show top 3 features
                mean_val = cluster_data[col].mean()
                cluster_summary += f"• {col}: {mean_val:.2f}\n"
        
        return cluster_summary
    
    def _trend_analysis(self, target_column):
        """Analyze trends in specified column"""
        if not target_column or target_column not in self.df.columns:
            return "❌ Please specify a valid target column for trend analysis"
        
        analysis = f"📈 **Trend Analysis: {target_column}**\n\n"
        
        if self.df[target_column].dtype in ['object', 'category']:
            # Categorical analysis
            value_counts = self.df[target_column].value_counts()
            analysis += f"**Category Distribution:**\n"
            for cat, count in value_counts.head(10).items():
                pct = (count / len(self.df)) * 100
                analysis += f"• {cat}: {count} ({pct:.1f}%)\n"
        else:
            # Numeric analysis
            col_data = pd.to_numeric(self.df[target_column], errors='coerce').fillna(0)
            
            analysis += f"**Statistical Summary:**\n"
            analysis += f"• Mean: {col_data.mean():.3f}\n"
            analysis += f"• Median: {col_data.median():.3f}\n"
            analysis += f"• Std Dev: {col_data.std():.3f}\n"
            analysis += f"• Range: {col_data.min():.3f} to {col_data.max():.3f}\n\n"
            
            # Trend detection (simple linear regression)
            if len(col_data) > 5:
                X = np.arange(len(col_data)).reshape(-1, 1)
                y = col_data.values
                
                lr = LinearRegression()
                lr.fit(X, y)
                
                slope = lr.coef_[0]
                r_squared = lr.score(X, y)
                
                trend_direction = "📈 Increasing" if slope > 0 else "📉 Decreasing" if slope < 0 else "➡️ Stable"
                analysis += f"**Trend Detection:**\n"
                analysis += f"• Direction: {trend_direction}\n"
                analysis += f"• Slope: {slope:.6f}\n"
                analysis += f"• R²: {r_squared:.3f}\n"
        
        return analysis
    
    def _create_overview_plot(self):
        """Create overview visualization"""
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle('Data Overview Dashboard', fontsize=16, fontweight='bold')
        
        # Data types distribution
        dtype_counts = self.df.dtypes.value_counts()
        axes[0,0].pie(dtype_counts.values, labels=dtype_counts.index, autopct='%1.1f%%')
        axes[0,0].set_title('Data Types Distribution')
        
        # Missing data heatmap
        if self.df.isnull().sum().sum() > 0:
            sns.heatmap(self.df.isnull(), cbar=True, ax=axes[0,1], cmap='viridis')
            axes[0,1].set_title('Missing Data Pattern')
        else:
            axes[0,1].text(0.5, 0.5, 'No Missing Data', ha='center', va='center', transform=axes[0,1].transAxes)
            axes[0,1].set_title('Missing Data Pattern')
        
        # Numeric columns distribution
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            self.df[numeric_cols].hist(ax=axes[1,0], bins=20)
            axes[1,0].set_title('Numeric Distributions')
        else:
            axes[1,0].text(0.5, 0.5, 'No Numeric Data', ha='center', va='center', transform=axes[1,0].transAxes)
            axes[1,0].set_title('Numeric Distributions')
        
        # Row count over index
        axes[1,1].plot(range(len(self.df)), [1]*len(self.df), 'o-', markersize=1)
        axes[1,1].set_title(f'Data Points ({len(self.df)} rows)')
        axes[1,1].set_xlabel('Index')
        
        plt.tight_layout()
        return fig
    
    def _create_correlation_plot(self):
        """Create correlation heatmap"""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) < 2:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(0.5, 0.5, 'Need at least 2 numeric columns\nfor correlation analysis', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_title('Correlation Analysis')
            return fig
        
        fig, ax = plt.subplots(figsize=(10, 8))
        corr_matrix = self.df[numeric_cols].corr()
        
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        sns.heatmap(corr_matrix, mask=mask, annot=True, cmap='coolwarm', center=0,
                   square=True, linewidths=0.5, cbar_kws={"shrink": .8}, ax=ax)
        ax.set_title('Correlation Matrix Heatmap', fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    def _create_missing_data_plot(self):
        """Create missing data visualization"""
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        
        missing = self.df.isnull().sum()
        missing_pct = (missing / len(self.df)) * 100
        
        # Missing data bar chart
        missing_data = missing[missing > 0]
        if len(missing_data) > 0:
            missing_data.plot(kind='bar', ax=axes[0], color='coral')
            axes[0].set_title('Missing Data Count by Column')
            axes[0].set_ylabel('Missing Count')
            axes[0].tick_params(axis='x', rotation=45)
            
            # Missing data percentage
            missing_pct_data = missing_pct[missing_pct > 0]
            missing_pct_data.plot(kind='bar', ax=axes[1], color='lightcoral')
            axes[1].set_title('Missing Data Percentage by Column')
            axes[1].set_ylabel('Missing Percentage (%)')
            axes[1].tick_params(axis='x', rotation=45)
        else:
            for ax in axes:
                ax.text(0.5, 0.5, 'No Missing Data Found!', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=14, color='green', fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    def _create_cluster_plot(self):
        """Create clustering visualization"""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) < 2 or 'Cluster' not in self.df.columns:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(0.5, 0.5, 'Clustering visualization requires\nat least 2 numeric columns', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)
            return fig
        
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        
        # Scatter plot of first two numeric columns
        col1, col2 = numeric_cols[0], numeric_cols[1]
        scatter = axes[0].scatter(self.df[col1], self.df[col2], c=self.df['Cluster'], 
                                 cmap='viridis', alpha=0.7)
        axes[0].set_xlabel(col1)
        axes[0].set_ylabel(col2)
        axes[0].set_title(f'Clusters: {col1} vs {col2}')
        plt.colorbar(scatter, ax=axes[0])
        
        # Cluster size distribution
        cluster_counts = self.df['Cluster'].value_counts().sort_index()
        axes[1].bar(cluster_counts.index, cluster_counts.values, color='skyblue')
        axes[1].set_xlabel('Cluster ID')
        axes[1].set_ylabel('Number of Points')
        axes[1].set_title('Cluster Size Distribution')
        
        plt.tight_layout()
        return fig
    
    def _create_trend_plot(self, target_column):
        """Create trend visualization"""
        if not target_column or target_column not in self.df.columns:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(0.5, 0.5, 'Please specify a valid target column', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)
            return fig
        
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        
        if self.df[target_column].dtype in ['object', 'category']:
            # Categorical data
            value_counts = self.df[target_column].value_counts()
            
            # Bar chart
            value_counts.head(10).plot(kind='bar', ax=axes[0], color='lightblue')
            axes[0].set_title(f'{target_column} - Top 10 Categories')
            axes[0].tick_params(axis='x', rotation=45)
            
            # Pie chart
            top_categories = value_counts.head(8)
            if len(value_counts) > 8:
                others_count = value_counts[8:].sum()
                top_categories['Others'] = others_count
            
            axes[1].pie(top_categories.values, labels=top_categories.index, autopct='%1.1f%%')
            axes[1].set_title(f'{target_column} - Distribution')
        else:
            # Numeric data
            col_data = pd.to_numeric(self.df[target_column], errors='coerce').fillna(0)
            
            # Line plot
            axes[0].plot(col_data.values, 'b-', alpha=0.7, linewidth=1)
            axes[0].set_title(f'{target_column} - Trend Over Index')
            axes[0].set_xlabel('Index')
            axes[0].set_ylabel(target_column)
            
            # Add trend line
            X = np.arange(len(col_data)).reshape(-1, 1)
            y = col_data.values
            lr = LinearRegression()
            lr.fit(X, y)
            trend_line = lr.predict(X)
            axes[0].plot(trend_line, 'r--', linewidth=2, label=f'Trend (slope: {lr.coef_[0]:.4f})')
            axes[0].legend()
            
            # Histogram
            axes[1].hist(col_data, bins=30, alpha=0.7, color='lightgreen', edgecolor='black')
            axes[1].set_title(f'{target_column} - Distribution')
            axes[1].set_xlabel(target_column)
            axes[1].set_ylabel('Frequency')
        
        plt.tight_layout()
        return fig
    
    def _export_enhanced(self):
        """Export data with analysis results"""
        if self.df is None:
            return "No data to export"
        
        export_summary = f"📤 **Enhanced Data Export**\n\n"
        export_summary += f"• **Original Shape**: {self.df.shape}\n"
        export_summary += f"• **Export Timestamp**: {pd.Timestamp.now()}\n\n"
        
        # Add data quality metrics
        quality_score = 100
        missing_pct = (self.df.isnull().sum().sum() / (self.df.shape[0] * self.df.shape[1])) * 100
        quality_score -= missing_pct
        
        export_summary += f"**Data Quality Metrics:**\n"
        export_summary += f"• **Missing Data**: {missing_pct:.1f}%\n"
        export_summary += f"• **Quality Score**: {quality_score:.1f}/100\n\n"
        
        # Export options
        export_summary += f"**Available Export Formats:**\n"
        export_summary += f"• CSV: {self.df.shape[0]} rows ready\n"
        export_summary += f"• JSON: Structured format\n"
        export_summary += f"• Excel: Multiple sheets with analysis\n\n"
        
        # Sample enhanced data
        export_summary += f"**Enhanced Data Sample:**\n"
        export_summary += self.df.head().to_string()
        
        return export_summary

# Create processor instance
processor = DataProcessorAgent()

# Enhanced interface
with gr.Blocks(title="📊 Data Processor Pro", theme=gr.themes.Soft()) as interface:
    gr.Markdown("""
    # 📊 Data Processor Pro Agent
    **Advanced data analysis with ML-powered insights and visualizations**
    
    Upload CSV/JSON files for comprehensive analysis including clustering, trend detection, and statistical insights.
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            file_upload = gr.File(
                label="📁 Upload Data File",
                file_types=[".csv", ".json"],
                type="binary"
            )
            
            analysis_type = gr.Dropdown(
                choices=[
                    "Data Overview", 
                    "Statistical Summary", 
                    "Missing Data Analysis",
                    "Clustering Analysis",
                    "Trend Analysis",
                    "Export Enhanced"
                ],
                label="Analysis Type",
                value="Data Overview"
            )
            
            target_column = gr.Dropdown(
                choices=[],
                label="Target Column (for Trend Analysis)",
                visible=False,
                interactive=True
            )
            
            analyze_btn = gr.Button("🔍 Run Analysis", variant="primary", size="lg")
            
        with gr.Column(scale=2):
            analysis_output = gr.Textbox(label="Analysis Results", lines=15, max_lines=25)
            status_output = gr.Textbox(label="Status", lines=2, interactive=False)
    
    with gr.Row():
        plot_output = gr.Plot(label="Visualization", visible=True)
    
    def update_target_column_choices(file_content):
        """Update target column choices based on uploaded file"""
        if not file_content:
            return gr.update(choices=[], visible=False)
        
        try:
            content = file_content.decode('utf-8')
            # Try to parse and get columns
            try:
                data = json.loads(content)
                if isinstance(data, list) and len(data) > 0:
                    columns = list(data[0].keys()) if isinstance(data[0], dict) else []
                else:
                    columns = []
            except:
                try:
                    df_temp = pd.read_csv(io.StringIO(content))
                    columns = df_temp.columns.tolist()
                except:
                    columns = []
            
            return gr.update(choices=columns, visible=True)
        except:
            return gr.update(choices=[], visible=False)
    
    def toggle_target_column(analysis_type):
        """Show target column dropdown for trend analysis"""
        return gr.update(visible=(analysis_type == "Trend Analysis"))
    
    # Event handlers
    file_upload.change(
        update_target_column_choices,
        inputs=[file_upload],
        outputs=[target_column]
    )
    
    analysis_type.change(
        toggle_target_column,
        inputs=[analysis_type],
        outputs=[target_column]
    )
    
    analyze_btn.click(
        processor.load_and_analyze,
        inputs=[file_upload, analysis_type, target_column],
        outputs=[analysis_output, plot_output, status_output]
    )

if __name__ == "__main__":
    interface.launch(server_port=int(os.environ.get('AGENT_PORT', 7860)))
