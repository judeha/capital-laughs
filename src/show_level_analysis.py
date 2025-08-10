import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import holidays
import glob
import os
from collections import Counter, defaultdict
import json

class ShowLevelAnalysis:
    def __init__(self, data_folder='src/data'):
        self.data_folder = data_folder
        self.df = None
        self.us_holidays = holidays.US()
        self.show_metrics = {}
        
    def load_data(self):
        """Load all CSV files and combine them"""
        csv_files = glob.glob(os.path.join(self.data_folder, '*.csv'))
        dataframes = []
        
        for file in csv_files:
            if file.endswith('.csv') and not 'eda' in file.lower():
                day_name = os.path.basename(file).replace('.csv', '')
                df_temp = pd.read_csv(file)
                df_temp['day_of_week'] = day_name
                dataframes.append(df_temp)
                print(f"Loaded {len(df_temp)} records from {day_name}")
        
        self.df = pd.concat(dataframes, ignore_index=True)
        print(f"Total records loaded: {len(self.df)}")
        
        # Clean and prepare data
        self.prepare_data()
        
    def prepare_data(self):
        """Clean and prepare the data for analysis"""
        # Convert date columns
        self.df['Order date'] = pd.to_datetime(self.df['Order date'])
        self.df['Event start date'] = pd.to_datetime(self.df['Event start date'])
        
        # Calculate days between order and event
        self.df['days_before_event'] = (self.df['Event start date'] - self.df['Order date']).dt.days
        
        # Extract time components
        self.df['order_hour'] = self.df['Order date'].dt.hour
        self.df['order_day_of_week'] = self.df['Order date'].dt.day_name()
        self.df['order_month'] = self.df['Order date'].dt.month
        self.df['order_year'] = self.df['Order date'].dt.year
        self.df['order_week'] = self.df['Order date'].dt.isocalendar().week
        
        # Event date components
        self.df['event_month'] = self.df['Event start date'].dt.month
        self.df['event_year'] = self.df['Event start date'].dt.year
        self.df['event_week'] = self.df['Event start date'].dt.isocalendar().week
        
        # Clean revenue columns
        revenue_cols = ['Gross sales', 'Ticket revenue', 'Net sales']
        for col in revenue_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        
        # Create customer identifier
        self.df['customer_id'] = self.df['Buyer email'].str.lower()
        
        # Create unique show identifier
        self.df['show_id'] = self.df['Event start date'].astype(str) + '_' + self.df['day_of_week']
        
    def analyze_individual_shows(self):
        """Analyze each individual show performance"""
        show_analysis = {}
        
        # Group by individual shows
        show_groups = self.df.groupby(['Event start date', 'day_of_week', 'Event name'])
        
        for (event_date, day_of_week, event_name), show_data in show_groups:
            show_key = f"{event_date}_{day_of_week}"
            
            # Basic metrics
            total_orders = len(show_data)
            total_tickets = show_data['Ticket quantity'].sum()
            total_revenue = show_data['Gross sales'].sum()
            unique_customers = show_data['customer_id'].nunique()
            
            # Timing metrics
            avg_days_before = show_data['days_before_event'].mean()
            same_day_purchases = len(show_data[show_data['days_before_event'] == 0])
            advance_purchases = len(show_data[show_data['days_before_event'] >= 7])
            
            # Customer analysis
            repeat_customers_for_show = 0
            customer_orders = show_data['customer_id'].value_counts()
            repeat_customers_for_show = len(customer_orders[customer_orders > 1])
            
            # Payment analysis
            free_tickets = len(show_data[show_data['Payment type'] == 'Free'])
            paid_tickets = total_orders - free_tickets
            
            # Geographic concentration
            state_mode = show_data['Purchaser state'].mode()
            top_state = state_mode.iloc[0] if len(state_mode) > 0 else 'Unknown'
            state_counts = show_data['Purchaser state'].value_counts()
            state_concentration = state_counts.iloc[0] / total_orders if len(state_counts) > 0 and total_orders > 0 else 0
            
            show_analysis[show_key] = {
                'event_date': event_date,
                'day_of_week': day_of_week,
                'event_name': event_name,
                'total_orders': total_orders,
                'total_tickets': total_tickets,
                'total_revenue': total_revenue,
                'unique_customers': unique_customers,
                'avg_order_value': total_revenue / total_orders if total_orders > 0 else 0,
                'tickets_per_order': total_tickets / total_orders if total_orders > 0 else 0,
                'avg_days_before': avg_days_before,
                'same_day_purchases': same_day_purchases,
                'same_day_rate': same_day_purchases / total_orders if total_orders > 0 else 0,
                'advance_purchases': advance_purchases,
                'advance_rate': advance_purchases / total_orders if total_orders > 0 else 0,
                'repeat_customers': repeat_customers_for_show,
                'repeat_rate': repeat_customers_for_show / unique_customers if unique_customers > 0 else 0,
                'free_tickets': free_tickets,
                'free_rate': free_tickets / total_orders if total_orders > 0 else 0,
                'paid_tickets': paid_tickets,
                'top_state': top_state,
                'state_concentration': state_concentration
            }
        
        return show_analysis
    
    def week_over_week_analysis(self, day_of_week):
        """Analyze week-over-week trends for a specific day"""
        day_data = self.df[self.df['day_of_week'] == day_of_week].copy()
        
        if len(day_data) == 0:
            return None
        
        # Group by week and event date
        weekly_shows = day_data.groupby(['event_year', 'event_week', 'Event start date']).agg({
            'Order ID': 'count',
            'Ticket quantity': 'sum',
            'Gross sales': 'sum',
            'customer_id': 'nunique',
            'days_before_event': 'mean'
        }).reset_index()
        
        weekly_shows.columns = ['Year', 'Week', 'Event_Date', 'Orders', 'Tickets', 'Revenue', 'Unique_Customers', 'Avg_Days_Before']
        weekly_shows = weekly_shows.sort_values(['Year', 'Week'])
        
        # Calculate week-over-week changes
        weekly_shows['Orders_WoW'] = weekly_shows['Orders'].pct_change() * 100
        weekly_shows['Revenue_WoW'] = weekly_shows['Revenue'].pct_change() * 100
        weekly_shows['Tickets_WoW'] = weekly_shows['Tickets'].pct_change() * 100
        
        return weekly_shows
    
    def identify_repeat_customer_case_studies(self):
        """Identify interesting repeat customer patterns"""
        customer_analysis = self.df.groupby('customer_id').agg({
            'Order ID': 'count',
            'Ticket quantity': 'sum',
            'Gross sales': 'sum',
            'Event start date': ['min', 'max', 'nunique'],
            'day_of_week': lambda x: list(set(x)),
            'Event name': lambda x: list(set(x)),
            'Purchaser state': 'first',
            'Purchaser city': 'first'
        }).reset_index()
        
        # Flatten column names
        customer_analysis.columns = ['customer_id', 'total_orders', 'total_tickets', 'total_spent', 
                                   'first_order', 'last_order', 'unique_events', 'days_attended', 
                                   'events_attended', 'state', 'city']
        
        # Calculate customer lifetime
        customer_analysis['customer_lifetime_days'] = (
            pd.to_datetime(customer_analysis['last_order']) - 
            pd.to_datetime(customer_analysis['first_order'])
        ).dt.days
        
        # Filter for interesting repeat customers
        repeat_customers = customer_analysis[customer_analysis['total_orders'] >= 3].copy()
        repeat_customers['avg_order_value'] = repeat_customers['total_spent'] / repeat_customers['total_orders']
        repeat_customers['days_variety'] = repeat_customers['days_attended'].apply(len)
        
        # Sort by different criteria for case studies
        case_studies = {
            'highest_spender': repeat_customers.nlargest(5, 'total_spent'),
            'most_frequent': repeat_customers.nlargest(5, 'total_orders'),
            'longest_relationship': repeat_customers.nlargest(5, 'customer_lifetime_days'),
            'most_diverse_attendance': repeat_customers.nlargest(5, 'days_variety'),
            'highest_avg_order': repeat_customers.nlargest(5, 'avg_order_value')
        }
        
        return case_studies
    
    def controllable_variables_analysis(self):
        """Analyze variables that showrunners can control to boost attendance"""
        controllable_insights = {}
        
        # 1. Day of week impact
        day_performance = self.df.groupby('day_of_week').agg({
            'Order ID': 'count',
            'Ticket quantity': 'sum',
            'Gross sales': 'sum'
        }).reset_index()
        day_performance['avg_orders_per_show'] = day_performance['Order ID'] / self.df.groupby('day_of_week')['Event start date'].nunique()
        
        # 2. Pricing strategy impact (free vs paid)
        pricing_impact = self.df.groupby('Payment type').agg({
            'Order ID': 'count',
            'Ticket quantity': 'sum',
            'customer_id': 'nunique'
        }).reset_index()
        
        # 3. Advance booking patterns
        booking_windows = pd.cut(self.df['days_before_event'], 
                               bins=[-1, 0, 1, 3, 7, 14, 30, float('inf')],
                               labels=['Same Day', '1 Day', '2-3 Days', '4-7 Days', '1-2 Weeks', '2-4 Weeks', '1+ Month'])
        
        booking_analysis = self.df.groupby(booking_windows).agg({
            'Order ID': 'count',
            'Ticket quantity': 'sum',
            'Gross sales': 'sum'
        }).reset_index()
        
        # 4. Seasonal patterns
        seasonal_analysis = self.df.groupby('event_month').agg({
            'Order ID': 'count',
            'Ticket quantity': 'sum',
            'Gross sales': 'sum'
        }).reset_index()
        
        # 5. Customer acquisition vs retention
        customer_types = []
        for _, row in self.df.iterrows():
            customer_orders = len(self.df[self.df['customer_id'] == row['customer_id']])
            if customer_orders == 1:
                customer_types.append('New')
            else:
                customer_types.append('Returning')
        
        self.df['customer_type'] = customer_types
        
        acquisition_analysis = self.df.groupby('customer_type').agg({
            'Order ID': 'count',
            'Gross sales': 'sum'
        }).reset_index()
        
        controllable_insights = {
            'day_performance': day_performance,
            'pricing_impact': pricing_impact,
            'booking_analysis': booking_analysis,
            'seasonal_analysis': seasonal_analysis,
            'acquisition_analysis': acquisition_analysis
        }
        
        return controllable_insights
    
    def generate_actionable_recommendations(self):
        """Generate specific recommendations for showrunners"""
        recommendations = []
        
        # Analyze the data for recommendations
        show_analysis = self.analyze_individual_shows()
        controllable_vars = self.controllable_variables_analysis()
        
        # Day of week recommendations
        best_day = controllable_vars['day_performance'].loc[
            controllable_vars['day_performance']['avg_orders_per_show'].idxmax(), 'day_of_week'
        ]
        recommendations.append(f"🗓️ SCHEDULING: {best_day} shows perform best with highest average attendance")
        
        # Pricing recommendations
        free_orders = controllable_vars['pricing_impact'][controllable_vars['pricing_impact']['Payment type'] == 'Free']['Order ID'].iloc[0]
        total_orders = controllable_vars['pricing_impact']['Order ID'].sum()
        free_percentage = (free_orders / total_orders) * 100
        
        if free_percentage > 15:
            recommendations.append(f"💰 PRICING: {free_percentage:.1f}% of tickets are free - consider reducing free tickets to boost revenue")
        
        # Booking window recommendations
        same_day_bookings = controllable_vars['booking_analysis'][
            controllable_vars['booking_analysis']['days_before_event'] == 'Same Day'
        ]['Order ID'].iloc[0] if len(controllable_vars['booking_analysis']) > 0 else 0
        
        if same_day_bookings > total_orders * 0.15:
            recommendations.append("📢 MARKETING: High same-day bookings suggest need for earlier promotion campaigns")
        
        # Customer retention recommendations
        returning_revenue = controllable_vars['acquisition_analysis'][
            controllable_vars['acquisition_analysis']['customer_type'] == 'Returning'
        ]['Gross sales'].iloc[0] if len(controllable_vars['acquisition_analysis']) > 0 else 0
        
        total_revenue = controllable_vars['acquisition_analysis']['Gross sales'].sum()
        returning_percentage = (returning_revenue / total_revenue) * 100
        
        recommendations.append(f"🔄 RETENTION: {returning_percentage:.1f}% of revenue from returning customers - focus on loyalty programs")
        
        # Seasonal recommendations
        best_month = controllable_vars['seasonal_analysis'].loc[
            controllable_vars['seasonal_analysis']['Order ID'].idxmax(), 'event_month'
        ]
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        recommendations.append(f"📅 SEASONAL: {month_names[int(best_month)-1]} shows perform best - consider more shows in this month")
        
        return recommendations
    
    def save_detailed_analysis(self, filename='detailed_show_analysis.json'):
        """Save comprehensive analysis to JSON"""
        analysis_results = {
            'individual_shows': self.analyze_individual_shows(),
            'controllable_variables': self.controllable_variables_analysis(),
            'recommendations': self.generate_actionable_recommendations(),
            'repeat_customer_case_studies': self.identify_repeat_customer_case_studies()
        }
        
        # Convert numpy types to native Python types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, pd.Timestamp):
                return obj.isoformat()
            elif isinstance(obj, pd.DataFrame):
                return obj.to_dict('records')
            return obj
        
        # Recursively convert all numpy types
        def recursive_convert(obj):
            if isinstance(obj, dict):
                return {k: recursive_convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [recursive_convert(item) for item in obj]
            else:
                return convert_numpy_types(obj)
        
        analysis_results = recursive_convert(analysis_results)
        
        with open(filename, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        
        print(f"Detailed analysis saved to {filename}")
        return analysis_results

def main():
    """Main analysis function"""
    print("Starting Show-Level Comedy Analysis...")
    
    analyzer = ShowLevelAnalysis()
    analyzer.load_data()
    
    print("\n" + "="*80)
    print("SHOW-LEVEL ANALYSIS RESULTS")
    print("="*80)
    
    # Individual show analysis
    show_analysis = analyzer.analyze_individual_shows()
    print(f"\n📊 ANALYZED {len(show_analysis)} INDIVIDUAL SHOWS")
    
    # Find best and worst performing shows
    shows_df = pd.DataFrame(show_analysis).T
    best_show = shows_df.loc[shows_df['total_orders'].idxmax()]
    worst_show = shows_df.loc[shows_df['total_orders'].idxmin()]
    
    print(f"\n🏆 BEST PERFORMING SHOW:")
    print(f"   Date: {best_show['event_date']}")
    print(f"   Day: {best_show['day_of_week']}")
    print(f"   Orders: {best_show['total_orders']}")
    print(f"   Revenue: ${best_show['total_revenue']:.2f}")
    
    print(f"\n📉 LOWEST PERFORMING SHOW:")
    print(f"   Date: {worst_show['event_date']}")
    print(f"   Day: {worst_show['day_of_week']}")
    print(f"   Orders: {worst_show['total_orders']}")
    print(f"   Revenue: ${worst_show['total_revenue']:.2f}")
    
    # Week-over-week analysis for each day
    print(f"\n📈 WEEK-OVER-WEEK ANALYSIS:")
    for day in ['Monday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
        wow_data = analyzer.week_over_week_analysis(day)
        if wow_data is not None and len(wow_data) > 1:
            avg_growth = wow_data['Orders_WoW'].mean()
            print(f"   {day}: Average WoW growth {avg_growth:.1f}%")
    
    # Repeat customer case studies
    case_studies = analyzer.identify_repeat_customer_case_studies()
    print(f"\n👥 REPEAT CUSTOMER CASE STUDIES:")
    
    if 'highest_spender' in case_studies and len(case_studies['highest_spender']) > 0:
        top_spender = case_studies['highest_spender'].iloc[0]
        print(f"   💰 Top Spender: ${top_spender['total_spent']:.2f} across {top_spender['total_orders']} orders")
        print(f"      Days attended: {top_spender['days_attended']}")
        print(f"      Customer lifetime: {top_spender['customer_lifetime_days']} days")
    
    if 'most_frequent' in case_studies and len(case_studies['most_frequent']) > 0:
        most_frequent = case_studies['most_frequent'].iloc[0]
        print(f"   🎭 Most Frequent: {most_frequent['total_orders']} orders, {most_frequent['unique_events']} different events")
    
    # Actionable recommendations
    recommendations = analyzer.generate_actionable_recommendations()
    print(f"\n🎯 ACTIONABLE RECOMMENDATIONS FOR SHOWRUNNERS:")
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")
    
    # Save detailed analysis
    analyzer.save_detailed_analysis()
    
    print(f"\n✅ Complete show-level analysis saved!")
    print(f"📈 Run 'streamlit run src/show_level_dashboard.py' for interactive visualizations")

if __name__ == "__main__":
    main()
