import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, timedelta
from scipy import signal
from scipy.stats import zscore
import warnings
warnings.filterwarnings('ignore')

class AdvancedTimeSeriesAnalysis:
    def __init__(self, df):
        self.df = df.copy()
        self.prepare_time_series_data()
    
    def prepare_time_series_data(self):
        """Prepare data for time series analysis"""
        # Ensure datetime columns
        self.df['Order date'] = pd.to_datetime(self.df['Order date'])
        self.df['Event start date'] = pd.to_datetime(self.df['Event start date'])
        
        # Create time-based features
        self.df['order_week'] = self.df['Order date'].dt.isocalendar().week
        self.df['order_year'] = self.df['Order date'].dt.year
        self.df['order_weekday'] = self.df['Order date'].dt.dayofweek
        self.df['order_hour'] = self.df['Order date'].dt.hour
        
        # Create daily aggregations
        self.daily_data = self.df.groupby(self.df['Order date'].dt.date).agg({
            'Order ID': 'count',
            'Gross sales': 'sum',
            'Ticket quantity': 'sum',
            'customer_id': 'nunique'
        }).reset_index()
        self.daily_data.columns = ['Date', 'Orders', 'Revenue', 'Tickets', 'Unique_Customers']
        self.daily_data['Date'] = pd.to_datetime(self.daily_data['Date'])
        self.daily_data = self.daily_data.sort_values('Date')
        
        # Create weekly aggregations
        self.weekly_data = self.df.groupby([
            self.df['Order date'].dt.isocalendar().year,
            self.df['Order date'].dt.isocalendar().week
        ]).agg({
            'Order ID': 'count',
            'Gross sales': 'sum',
            'Ticket quantity': 'sum',
            'customer_id': 'nunique'
        }).reset_index()
        self.weekly_data.columns = ['Year', 'Week', 'Orders', 'Revenue', 'Tickets', 'Unique_Customers']
        
        # Create week start dates for plotting
        self.weekly_data['Week_Start'] = pd.to_datetime(
            self.weekly_data['Year'].astype(str) + '-W' + 
            self.weekly_data['Week'].astype(str).str.zfill(2) + '-1', 
            format='%Y-W%W-%w'
        )
        self.weekly_data = self.weekly_data.sort_values('Week_Start')
    
    def apply_smoothing(self, data, method='rolling', window=7, alpha=0.3):
        """Apply various smoothing techniques"""
        if method == 'rolling':
            return data.rolling(window=window, center=True).mean()
        elif method == 'exponential':
            return data.ewm(alpha=alpha).mean()
        elif method == 'savgol':
            if len(data) > window:
                return pd.Series(signal.savgol_filter(data, window, 3), index=data.index)
            else:
                return data
        else:
            return data
    
    def detect_anomalies(self, data, threshold=2):
        """Detect anomalies using z-score"""
        z_scores = np.abs(zscore(data.dropna()))
        return z_scores > threshold
    
    def analyze_weekly_patterns(self):
        """Analyze patterns by week of year"""
        weekly_patterns = self.df.groupby([
            self.df['Order date'].dt.isocalendar().week,
            self.df['day_of_week']
        ]).agg({
            'Order ID': 'count',
            'Gross sales': 'sum'
        }).reset_index()
        weekly_patterns.columns = ['Week', 'Day', 'Orders', 'Revenue']
        
        return weekly_patterns
    
    def create_interactive_time_series(self, metric='Orders', smoothing_method='rolling', 
                                     window=7, alpha=0.3, show_anomalies=True):
        """Create interactive time series plot with controls"""
        
        # Get data based on granularity
        data = self.daily_data.copy()
        
        # Apply smoothing
        smoothed_data = self.apply_smoothing(data[metric], smoothing_method, window, alpha)
        
        # Create figure
        fig = go.Figure()
        
        # Add original data
        fig.add_trace(go.Scatter(
            x=data['Date'],
            y=data[metric],
            mode='lines+markers',
            name=f'Original {metric}',
            line=dict(color='lightblue', width=1),
            marker=dict(size=3),
            opacity=0.6
        ))
        
        # Add smoothed data
        fig.add_trace(go.Scatter(
            x=data['Date'],
            y=smoothed_data,
            mode='lines',
            name=f'Smoothed {metric}',
            line=dict(color='red', width=2)
        ))
        
        # Add anomalies if requested
        if show_anomalies:
            anomalies = self.detect_anomalies(data[metric])
            if anomalies.any():
                anomaly_dates = data.loc[anomalies, 'Date']
                anomaly_values = data.loc[anomalies, metric]
                
                fig.add_trace(go.Scatter(
                    x=anomaly_dates,
                    y=anomaly_values,
                    mode='markers',
                    name='Anomalies',
                    marker=dict(color='orange', size=8, symbol='diamond')
                ))
        
        # Update layout
        fig.update_layout(
            title=f'{metric} Over Time with {smoothing_method.title()} Smoothing',
            xaxis_title='Date',
            yaxis_title=metric,
            hovermode='x unified',
            showlegend=True,
            height=500
        )
        
        # Add range selector
        fig.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=30, label="30D", step="day", stepmode="backward"),
                        dict(count=90, label="3M", step="day", stepmode="backward"),
                        dict(count=180, label="6M", step="day", stepmode="backward"),
                        dict(count=365, label="1Y", step="day", stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(visible=True),
                type="date"
            )
        )
        
        return fig
    
    def create_weekly_heatmap(self):
        """Create heatmap showing weekly patterns by day of week"""
        weekly_patterns = self.analyze_weekly_patterns()
        
        # Pivot for heatmap
        heatmap_data = weekly_patterns.pivot(index='Week', columns='Day', values='Orders')
        
        # Reorder columns by weekday
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_data = heatmap_data.reindex(columns=[d for d in day_order if d in heatmap_data.columns])
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale='Viridis',
            hoverongaps=False
        ))
        
        fig.update_layout(
            title='Weekly Order Patterns by Day of Week',
            xaxis_title='Day of Week',
            yaxis_title='Week of Year',
            height=600
        )
        
        return fig
    
    def create_customer_lifecycle_gantt(self, top_n=20, order="top"):
        """Create Gantt-like chart for repeat customer lifecycles"""
        
        # Get repeat customers
        customer_analysis = self.df.groupby('customer_id').agg({
            'Order date': ['min', 'max', 'count'],
            'Gross sales': 'sum',
            'day_of_week': lambda x: list(set(x))
        }).reset_index()
        
        # Flatten column names
        customer_analysis.columns = ['customer_id', 'first_order', 'last_order', 'total_orders', 'total_spent', 'days_attended']
        
        # Filter for repeat customers and get either top or bottom spenders
        repeat_customers = customer_analysis[customer_analysis['total_orders'] >= 3]
        if order == "top":
            top_customers = repeat_customers.nlargest(top_n, 'total_spent')
        else:
            top_customers = repeat_customers.nsmallest(top_n, 'total_spent')

        # Calculate customer lifetime
        top_customers['lifetime_days'] = (
            pd.to_datetime(top_customers['last_order']) - 
            pd.to_datetime(top_customers['first_order'])
        ).dt.days
        
        # Create Gantt chart
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set3
        
        for i, (_, customer) in enumerate(top_customers.iterrows()):
            # Get all orders for this customer
            customer_orders = self.df[self.df['customer_id'] == customer['customer_id']].copy()
            customer_orders = customer_orders.sort_values('Order date')
            
            # Add customer lifecycle bar
            fig.add_trace(go.Scatter(
                x=[customer['first_order'], customer['last_order']],
                y=[i, i],
                mode='lines',
                line=dict(color=colors[i % len(colors)], width=8),
                name=f"Customer {i+1}",
                hovertemplate=f"<b>Customer {i+1}</b><br>" +
                            f"Orders: {customer['total_orders']}<br>" +
                            f"Spent: ${customer['total_spent']:.2f}<br>" +
                            f"Days: {customer['days_attended']}<br>" +
                            f"Lifetime: {customer['lifetime_days']} days<extra></extra>"
            ))
            
            # Add individual order points
            fig.add_trace(go.Scatter(
                x=customer_orders['Order date'],
                y=[i] * len(customer_orders),
                mode='markers',
                marker=dict(
                    color=colors[i % len(colors)],
                    size=8,
                    symbol='circle',
                    line=dict(color='white', width=1)
                ),
                showlegend=False,
                hovertemplate="<b>Order</b><br>" +
                            "Date: %{x}<br>" +
                            "Amount: $" + customer_orders['Gross sales'].astype(str) + "<extra></extra>"
            ))
        
        fig.update_layout(
            title=f'Customer Lifecycle Timeline - Top {top_n} Repeat Customers',
            xaxis_title='Date',
            yaxis_title='Customer Rank (by Total Spent)',
            yaxis=dict(
                tickmode='array',
                tickvals=list(range(len(top_customers))),
                ticktext=[f'Customer {i+1}' for i in range(len(top_customers))]
            ),
            height=max(400, len(top_customers) * 25),
            hovermode='closest'
        )
        
        return fig
    
def show_gantt_customer_subheader(analyzer):
    """Display Gantt chart for customer lifecycles"""
    
    # Show filtering - similar to Individual Shows
    show_filter = st.sidebar.selectbox(
        "Filter by Show Day",
        ["All Shows"] + list(analyzer.df['day_of_week'].unique())
    )
    
    # Filter data based on selection
    if show_filter != "All Shows":
        filtered_df = analyzer.df[analyzer.df['day_of_week'] == show_filter].copy()
        st.info(f"📊 Analyzing {show_filter} shows only ({len(filtered_df)} orders)")
    else:
        filtered_df = analyzer.df.copy()
        st.info(f"📊 Analyzing all shows ({len(filtered_df)} orders)")
    
    # Initialize time series analyzer with filtered data
    ts_analyzer = AdvancedTimeSeriesAnalysis(filtered_df)
    
    # Customer lifecycle Gantt chart
    st.subheader("👥 Customer Lifecycle Timeline")
    
    top_n = st.slider("Number of Top Customers to Show", 10, 50, 20)
    gantt_fig = ts_analyzer.create_customer_lifecycle_gantt(top_n=top_n)
    st.plotly_chart(gantt_fig, use_container_width=True)

def show_advanced_time_series_tab(analyzer):
    """Display advanced time series analysis tab"""
    st.header("📈 Advanced Time Series Analysis")
    
    # Sidebar controls
    st.sidebar.subheader("Time Series Controls")
    
    # Show filtering - similar to Individual Shows
    show_filter = st.sidebar.selectbox(
        "Filter by Show Day",
        ["All Shows"] + list(analyzer.df['day_of_week'].unique())
    )
    
    # Filter data based on selection
    if show_filter != "All Shows":
        filtered_df = analyzer.df[analyzer.df['day_of_week'] == show_filter].copy()
        st.info(f"📊 Analyzing {show_filter} shows only ({len(filtered_df)} orders)")
    else:
        filtered_df = analyzer.df.copy()
        st.info(f"📊 Analyzing all shows ({len(filtered_df)} orders)")
    
    # Initialize time series analyzer with filtered data
    ts_analyzer = AdvancedTimeSeriesAnalysis(filtered_df)
    
    # Metric selection
    metric = st.sidebar.selectbox(
        "Select Metric",
        ["Orders", "Revenue", "Tickets", "Unique_Customers"]
    )
    
    # Smoothing controls
    smoothing_method = st.sidebar.selectbox(
        "Smoothing Method",
        ["rolling", "exponential", "savgol", "none"]
    )
    
    if smoothing_method == "rolling":
        window = st.sidebar.slider("Rolling Window", 3, 30, 7)
        alpha = 0.3
    elif smoothing_method == "exponential":
        alpha = st.sidebar.slider("Alpha (Smoothing Factor)", 0.1, 1.0, 0.3)
        window = 7
    elif smoothing_method == "savgol":
        window = st.sidebar.slider("Savitzky-Golay Window", 5, 21, 7, step=2)
        alpha = 0.3
    else:
        window = 7
        alpha = 0.3
    
    show_anomalies = st.sidebar.checkbox("Show Anomalies", True)
    
    # Main time series plot
    st.subheader("📊 Interactive Time Series")
    
    if smoothing_method != "none":
        fig = ts_analyzer.create_interactive_time_series(
            metric=metric,
            smoothing_method=smoothing_method,
            window=window,
            alpha=alpha,
            show_anomalies=show_anomalies
        )
    else:
        # Simple plot without smoothing
        data = ts_analyzer.daily_data
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=data['Date'],
            y=data[metric],
            mode='lines+markers',
            name=metric,
            line=dict(width=2)
        ))
        fig.update_layout(
            title=f'{metric} Over Time',
            xaxis_title='Date',
            yaxis_title=metric,
            height=500
        )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Weekly patterns heatmap
    st.subheader("🔥 Weekly Patterns Heatmap")
    heatmap_fig = ts_analyzer.create_weekly_heatmap()
    st.plotly_chart(heatmap_fig, use_container_width=True)
    
    # Key insights
    st.subheader("🔍 Time Series Insights")
    
    # Calculate some insights
    daily_data = ts_analyzer.daily_data
    weekly_data = ts_analyzer.weekly_data
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_daily_orders = daily_data['Orders'].mean()
        st.metric("Avg Daily Orders", f"{avg_daily_orders:.1f}")
        
        # Trend analysis
        recent_avg = daily_data.tail(30)['Orders'].mean()
        older_avg = daily_data.head(30)['Orders'].mean()
        trend = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
        st.metric("30-Day Trend", f"{trend:+.1f}%")
    
    with col2:
        # Volatility
        volatility = daily_data['Orders'].std()
        st.metric("Daily Volatility", f"{volatility:.1f}")
        
        # Peak day
        peak_day = daily_data.loc[daily_data['Orders'].idxmax(), 'Date']
        st.metric("Peak Day", peak_day.strftime('%Y-%m-%d'))
    
    with col3:
        # Weekly growth
        if len(weekly_data) > 1:
            weekly_growth = weekly_data['Orders'].pct_change().mean() * 100
            st.metric("Avg Weekly Growth", f"{weekly_growth:+.1f}%")
        
        # Anomaly count
        anomalies = ts_analyzer.detect_anomalies(daily_data['Orders'])
        anomaly_count = anomalies.sum()
        st.metric("Anomaly Days", f"{anomaly_count}")
    
    # Insights text
    insights = [
        f"The time series shows {'high' if volatility > avg_daily_orders * 0.5 else 'moderate'} volatility with {anomaly_count} anomalous days detected",
        f"Recent 30-day trend shows {'growth' if trend > 0 else 'decline'} of {abs(trend):.1f}% compared to early period"
    ]
    
    for insight in insights:
        st.info(f"💡 {insight}")
