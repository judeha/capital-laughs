import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from show_insights import ShowInsights
from advanced_time_series import show_advanced_time_series_tab, show_gantt_customer_subheader
import json
import os
import subprocess
import sys

# Page config
st.set_page_config(
    page_title="Comedy Analysis",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #FF6B6B;
        text-align: center;
        margin-bottom: 2rem;
    }
    .insight-box {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #4dabf7;
        margin: 1rem 0;
    }
    .recommendation-box {
        background-color: #f0f9ff;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #0ea5e9;
        margin: 0.5rem 0;
    }
    .case-study-box {
        background-color: #fef3c7;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #f59e0b;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_show_analysis():
    """Load and cache the show analysis data"""
    analyzer = ShowInsights()
    analyzer.load_data()
    return analyzer

@st.cache_data
def load_basic_analysis_results():
    """Load basic analysis results from JSON file"""
    if os.path.exists('basic_analysis_results.json'):
        with open('basic_analysis_results.json', 'r') as f:
            return json.load(f)
    else:
        st.info("Running basic analysis... This may take a moment.")
        result = subprocess.run([sys.executable, 'src/basic_analysis.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            with open('analysis_results.json', 'r') as f:
                return json.load(f)
        else:
            st.error("Failed to run basic analysis. Please check the logs.")
            return None

def main():
    st.markdown('<h1 class="main-header">Comedy Analysis</h1>', unsafe_allow_html=True)
    
    # Load data
    with st.spinner("Loading analysis..."):
        analyzer = load_show_analysis()
        basic_analysis_results = load_basic_analysis_results()
    
    # Sidebar
    st.sidebar.title("📊 Show Analysis")
    analysis_section = st.sidebar.selectbox(
        "Choose Analysis Section",
        ["Overview", "Customer Analysis", "Time Series Analysis (Basic)", "Time Series Analysis (Advanced)", "Geographic Analysis"]
    )
    
    # Main content based on selection
    if analysis_section == "Overview":
        show_overview_analysis(analyzer)
    elif analysis_section == "Customer Analysis":
        show_customer_analysis(analyzer)
    elif analysis_section == "Time Series Analysis (Basic)":
        show_basic_time_series_analysis(analyzer)
    elif analysis_section == "Time Series Analysis (Advanced)":
        show_advanced_time_series_tab(analyzer)
    elif analysis_section == "Geographic Analysis":
        show_geographic_analysis(basic_analysis_results)

def show_overview_analysis(analyzer):
    st.header("🎯 Overview")
    
    # Get show results
    show_groups = analyzer.df.groupby(['Event start date', 'day_of_week'])
    show_results = []
    
    for (event_date, day_of_week), show_data in show_groups:
        total_orders = len(show_data)
        total_revenue = show_data['Gross sales'].sum()
        unique_customers = show_data['customer_id'].nunique()
        avg_days_before = show_data['days_before_event'].mean()
        same_day_purchases = len(show_data[show_data['days_before_event'] == 0])
        free_tickets = len(show_data[show_data['Payment type'] == 'Free'])
        
        show_results.append({
            'Date': event_date,
            'Day': day_of_week,
            'Orders': total_orders,
            'Revenue': total_revenue,
            'Customers': unique_customers,
            'Avg_Days_Before': avg_days_before,
            'Same_Day_Rate': same_day_purchases / total_orders if total_orders > 0 else 0,
            'Free_Rate': free_tickets / total_orders if total_orders > 0 else 0
        })
    
    shows_df = pd.DataFrame(show_results)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Shows Analyzed", f"{len(shows_df):,}")
    with col2:
        best_show = shows_df.loc[shows_df['Orders'].idxmax()]
        st.metric("Best Show Orders", f"{best_show['Orders']}")
    with col3:
        avg_orders = shows_df['Orders'].mean()
        st.metric("Avg Orders per Show", f"{avg_orders:.1f}")
    with col4:
        total_revenue = shows_df['Revenue'].sum()
        st.metric("Total Revenue", f"${total_revenue:,.2f}")

    # Show details table
    st.subheader("🔍 Your Top Shows")
    
    # Add filters
    col1, col2 = st.columns(2)
    with col1:
        selected_day = st.selectbox("Filter by Day", ['All'] + list(shows_df['Day'].unique()))
    with col2:
        min_orders = st.slider("Minimum Orders", 0, int(shows_df['Orders'].max()), 0)
    
    # Filter data
    filtered_df = shows_df.copy()
    if selected_day != 'All':
        filtered_df = filtered_df[filtered_df['Day'] == selected_day]
    filtered_df = filtered_df[filtered_df['Orders'] >= min_orders]
    
    # Display filtered results
    st.dataframe(
        filtered_df.sort_values('Orders', ascending=False),
        use_container_width=True,
        hide_index=True
    )

        # Day of week performance
    day_performance = analyzer.df.groupby('day_of_week').agg({
        'Order ID': 'count',
        'Gross sales': 'sum',
        'Event start date': 'nunique'
    }).reset_index()
    day_performance['avg_orders_per_show'] = day_performance['Order ID'] / day_performance['Event start date']
    day_performance['avg_revenue_per_show'] = day_performance['Gross sales'] / day_performance['Event start date']
    
    st.subheader("🗓️ Best Day to Hold a Show")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(day_performance.sort_values('avg_orders_per_show', ascending=False), 
                    x='day_of_week', y='avg_orders_per_show',
                    title="Average Orders per Show")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(day_performance.sort_values('avg_revenue_per_show', ascending=False), 
                    x='day_of_week', y='avg_revenue_per_show',
                    title="Average Revenue per Show")
        st.plotly_chart(fig, use_container_width=True)
    
    # Booking windows
    st.subheader("📈 Best Day to Sell Tickets")

        # Show performance charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Performance by day of week
        day_performance = shows_df.groupby('Day').agg({
            'Orders': 'mean',
            'Revenue': 'mean'
        }).reset_index()
        
        fig = px.bar(day_performance, x='Day', y='Orders',
                    title="Average Orders by Day of Week")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        booking_windows = pd.cut(analyzer.df['days_before_event'], 
                            bins=[-1, 0, 1, 3, 7, 14, 30, float('inf')],
                            labels=['Same Day', '1 Day', '2-3 Days', '4-7 Days', '1-2 Weeks', '2-4 Weeks', '1+ Month'])
        
        booking_analysis = analyzer.df.groupby(booking_windows, observed=True).agg({
            'Order ID': 'count',
            'Gross sales': 'sum'
        }).reset_index()
        booking_analysis['avg_order_value'] = booking_analysis['Gross sales'] / booking_analysis['Order ID']
        
        fig = px.bar(booking_analysis, x='days_before_event', y='Order ID',
                    title="Orders by Booking Window")
        st.plotly_chart(fig, use_container_width=True)


def show_basic_time_series_analysis(analyzer):
    st.header("📈 Basic Time Series Analysis")
    
    # Analyze each day
    for day in ['Monday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
        day_data = analyzer.df[analyzer.df['day_of_week'] == day].copy()
        
        if len(day_data) == 0:
            continue
        
        st.subheader(f"📅 {day} Shows")
        
        # Group by event date
        daily_shows = day_data.groupby('Event start date').agg({
            'Order ID': 'count',
            'Gross sales': 'sum',
            'Ticket quantity': 'sum'
        }).reset_index()
        
        daily_shows = daily_shows.sort_values('Event start date')
        
        if len(daily_shows) > 1:
            # Calculate changes
            daily_shows['Orders_Change'] = daily_shows['Order ID'].pct_change() * 100
            daily_shows['Revenue_Change'] = daily_shows['Gross sales'].pct_change() * 100
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_growth = daily_shows['Orders_Change'].mean()
                st.metric(f"{day} Avg Order Growth", f"{avg_growth:.1f}%")
            
            with col2:
                revenue_growth = daily_shows['Revenue_Change'].mean()
                st.metric(f"{day} Avg Revenue Growth", f"{revenue_growth:.1f}%")
            
            with col3:
                total_shows = len(daily_shows)
                st.metric(f"Total {day} Shows", f"{total_shows}")
            
            # Chart showing trend
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=(f'{day} Orders Over Time', f'{day} Revenue Over Time'),
                vertical_spacing=0.1
            )
            
            fig.add_trace(
                go.Scatter(x=daily_shows['Event start date'], y=daily_shows['Order ID'],
                          mode='lines+markers', name='Orders'),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(x=daily_shows['Event start date'], y=daily_shows['Gross sales'],
                          mode='lines+markers', name='Revenue', line=dict(color='green')),
                row=2, col=1
            )
            
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

def show_customer_analysis(analyzer):

    show_gantt_customer_subheader(analyzer)

    # Case study categories
    st.subheader("🏆 Customer Case Studies")
        
    # Analyze customer behavior
    customer_analysis = analyzer.df.groupby('customer_id').agg({
        'Order ID': 'count',
        'Ticket quantity': 'sum',
        'Gross sales': 'sum',
        'Event start date': ['min', 'max'],
        'day_of_week': lambda x: list(set(x)),
        'Purchaser state': 'first',
        'Purchaser city': 'first'
    }).reset_index()
    
    # Flatten column names
    customer_analysis.columns = ['customer_id', 'total_orders', 'total_tickets', 'total_spent', 
                               'first_order', 'last_order', 'days_attended', 'state', 'city']
    
    # Filter for repeat customers
    repeat_customers = customer_analysis[customer_analysis['total_orders'] >= 3].copy()
    repeat_customers['avg_order_value'] = repeat_customers['total_spent'] / repeat_customers['total_orders']
    repeat_customers['days_variety'] = repeat_customers['days_attended'].apply(len)
    
    # Calculate customer lifetime
    repeat_customers['customer_lifetime_days'] = (
        pd.to_datetime(repeat_customers['last_order']) - 
        pd.to_datetime(repeat_customers['first_order'])
    ).dt.days
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Repeat Customers", f"{len(repeat_customers):,}")
    with col2:
        total_customers = analyzer.df['customer_id'].nunique()
        repeat_rate = len(repeat_customers) / total_customers * 100
        st.metric("Repeat Rate", f"{repeat_rate:.1f}%")
    with col3:
        avg_orders = repeat_customers['total_orders'].mean()
        st.metric("Avg Orders (Repeat)", f"{avg_orders:.1f}")
    with col4:
        total_repeat_revenue = repeat_customers['total_spent'].sum()
        st.metric("Repeat Customer Revenue", f"${total_repeat_revenue:,.2f}")
        
    case_study_type = st.selectbox(
        "Select Case Study Type",
        ["Top Spenders", "Most Frequent", "Most Diverse", "Longest Relationship"]
    )
    
    if case_study_type == "Top Spenders":
        top_customers = repeat_customers.nlargest(5, 'total_spent')
        st.markdown("### 💰 Top Spending Customers")
        
        for i, (_, customer) in enumerate(top_customers.iterrows(), 1):
            st.markdown(f"""
            <div class="case-study-box">
                <strong>Customer #{i} - {customer['city']}, {customer['state']}</strong><br>
                💰 Total Spent: ${customer['total_spent']:.2f}<br>
                🎫 Total Orders: {customer['total_orders']}<br>
                📅 Days Attended: {customer['days_attended']}<br>
                ⏱️ Customer Lifetime: {customer['customer_lifetime_days']} days<br>
                💵 Avg Order Value: ${customer['avg_order_value']:.2f}
            </div>
            """, unsafe_allow_html=True)
    
    elif case_study_type == "Most Frequent":
        most_frequent = repeat_customers.nlargest(5, 'total_orders')
        st.markdown("### 🎭 Most Frequent Attendees")
        
        for i, (_, customer) in enumerate(most_frequent.iterrows(), 1):
            st.markdown(f"""
            <div class="case-study-box">
                <strong>Customer #{i} - {customer['city']}, {customer['state']}</strong><br>
                🎫 Total Orders: {customer['total_orders']}<br>
                💰 Total Spent: ${customer['total_spent']:.2f}<br>
                🌟 Days Variety: {customer['days_variety']} different days<br>
                📅 Days Attended: {customer['days_attended']}<br>
                💵 Avg Order Value: ${customer['avg_order_value']:.2f}
            </div>
            """, unsafe_allow_html=True)
    
    elif case_study_type == "Most Diverse":
        most_diverse = repeat_customers.nlargest(5, 'days_variety')
        st.markdown("### 🌟 Most Diverse Attendance")
        
        for i, (_, customer) in enumerate(most_diverse.iterrows(), 1):
            st.markdown(f"""
            <div class="case-study-box">
                <strong>Customer #{i} - {customer['city']}, {customer['state']}</strong><br>
                🌟 Attends {customer['days_variety']} different days: {customer['days_attended']}<br>
                🎫 Total Orders: {customer['total_orders']}<br>
                💰 Total Spent: ${customer['total_spent']:.2f}<br>
                ⏱️ Customer Lifetime: {customer['customer_lifetime_days']} days
            </div>
            """, unsafe_allow_html=True)
    
    elif case_study_type == "Longest Relationship":
        longest_relationship = repeat_customers.nlargest(5, 'customer_lifetime_days')
        st.markdown("### ⏱️ Longest Customer Relationships")
        
        for i, (_, customer) in enumerate(longest_relationship.iterrows(), 1):
            st.markdown(f"""
            <div class="case-study-box">
                <strong>Customer #{i} - {customer['city']}, {customer['state']}</strong><br>
                ⏱️ Customer Lifetime: {customer['customer_lifetime_days']} days<br>
                🎫 Total Orders: {customer['total_orders']}<br>
                💰 Total Spent: ${customer['total_spent']:.2f}<br>
                📅 Days Attended: {customer['days_attended']}<br>
                💵 Avg Order Value: ${customer['avg_order_value']:.2f}
            </div>
            """, unsafe_allow_html=True)

def show_geographic_analysis(results):
    st.header("🗺️ Geographic Analysis")
    
    # Top states
    st.subheader("🏛️ Top States by Orders")
    
    if 'top_states' in results:
        states_data = results['top_states']
        st.bar_chart(states_data)
        
        # State insights
        total_orders = results['total_orders']
        dc_orders = states_data.get('DC', 0)
        dc_percentage = dc_orders / total_orders * 100
        
        st.info(f"🏛️ DC dominates with {dc_orders:,} orders ({dc_percentage:.1f}% of all orders)")
        st.info(f"DC area (DC, MD, VA) accounts for {sum(results['top_states'].get(state, 0) for state in ['DC', 'MD', 'VA']):,} orders")
    
    # Top cities
    st.subheader("🏙️ Top Cities by Orders")
    
    if 'top_cities' in results:
        cities_data = results['top_cities']
        # Remove empty city names
        cities_filtered = {k: v for k, v in cities_data.items() if k.strip()}
        st.bar_chart(cities_filtered)


if __name__ == "__main__":
    main()
