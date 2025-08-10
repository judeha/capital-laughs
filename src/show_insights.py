import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import glob
import os
import json

class ShowInsights:
    def __init__(self, data_folder='src/data'):
        self.data_folder = data_folder
        self.df = None
        
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
        
        # Clean revenue columns
        revenue_cols = ['Gross sales', 'Ticket revenue', 'Net sales']
        for col in revenue_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        
        # Create customer identifier
        self.df['customer_id'] = self.df['Buyer email'].str.lower()
        
    def analyze_individual_shows(self):
        """Analyze each individual show performance"""
        print("\n" + "="*60)
        print("INDIVIDUAL SHOW ANALYSIS")
        print("="*60)
        
        # Group by individual shows
        show_groups = self.df.groupby(['Event start date', 'day_of_week'])
        
        show_results = []
        for (event_date, day_of_week), show_data in show_groups:
            total_orders = len(show_data)
            total_revenue = show_data['Gross sales'].sum()
            unique_customers = show_data['customer_id'].nunique()
            avg_days_before = show_data['days_before_event'].mean()
            same_day_purchases = len(show_data[show_data['days_before_event'] == 0])
            free_tickets = len(show_data[show_data['Payment type'] == 'Free'])
            
            show_results.append({
                'date': event_date,
                'day': day_of_week,
                'orders': total_orders,
                'revenue': total_revenue,
                'customers': unique_customers,
                'avg_days_before': avg_days_before,
                'same_day_rate': same_day_purchases / total_orders if total_orders > 0 else 0,
                'free_rate': free_tickets / total_orders if total_orders > 0 else 0
            })
        
        # Sort by orders to find best/worst
        show_results.sort(key=lambda x: x['orders'], reverse=True)
        
        print(f"\n🏆 TOP 5 PERFORMING SHOWS:")
        for i, show in enumerate(show_results[:5], 1):
            print(f"   {i}. {show['date']} ({show['day']}): {show['orders']} orders, ${show['revenue']:.2f}")
        
        print(f"\n📉 BOTTOM 5 PERFORMING SHOWS:")
        for i, show in enumerate(show_results[-5:], 1):
            print(f"   {i}. {show['date']} ({show['day']}): {show['orders']} orders, ${show['revenue']:.2f}")
        
        return show_results
    
    def week_over_week_analysis(self):
        """Analyze week-over-week trends for each day"""
        print("\n" + "="*60)
        print("WEEK-OVER-WEEK ANALYSIS BY DAY")
        print("="*60)
        
        for day in ['Monday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
            day_data = self.df[self.df['day_of_week'] == day].copy()
            
            if len(day_data) == 0:
                continue
                
            # Group by event date to get show-level data
            daily_shows = day_data.groupby('Event start date').agg({
                'Order ID': 'count',
                'Gross sales': 'sum',
                'Ticket quantity': 'sum'
            }).reset_index()
            
            daily_shows = daily_shows.sort_values('Event start date')
            
            if len(daily_shows) > 1:
                # Calculate week-over-week changes
                daily_shows['orders_change'] = daily_shows['Order ID'].pct_change() * 100
                daily_shows['revenue_change'] = daily_shows['Gross sales'].pct_change() * 100
                
                avg_order_growth = daily_shows['orders_change'].mean()
                avg_revenue_growth = daily_shows['revenue_change'].mean()
                
                print(f"\n📈 {day.upper()} SHOWS:")
                print(f"   Total shows analyzed: {len(daily_shows)}")
                print(f"   Average order growth: {avg_order_growth:.1f}%")
                print(f"   Average revenue growth: {avg_revenue_growth:.1f}%")
                
                # Show specific examples
                if len(daily_shows) >= 3:
                    recent_shows = daily_shows.tail(3)
                    print(f"   Recent performance:")
                    for _, show in recent_shows.iterrows():
                        change_str = f"{show['orders_change']:+.1f}%" if not pd.isna(show['orders_change']) else "N/A"
                        print(f"     {show['Event start date']}: {show['Order ID']} orders ({change_str})")
    
    def repeat_customer_case_studies(self):
        """Identify interesting repeat customer patterns"""
        print("\n" + "="*60)
        print("REPEAT CUSTOMER CASE STUDIES")
        print("="*60)
        
        # Analyze customer behavior
        customer_analysis = self.df.groupby('customer_id').agg({
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
        
        # Filter for repeat customers (3+ orders)
        repeat_customers = customer_analysis[customer_analysis['total_orders'] >= 3].copy()
        repeat_customers['avg_order_value'] = repeat_customers['total_spent'] / repeat_customers['total_orders']
        repeat_customers['days_variety'] = repeat_customers['days_attended'].apply(len)
        
        # Calculate customer lifetime
        repeat_customers['customer_lifetime_days'] = (
            pd.to_datetime(repeat_customers['last_order']) - 
            pd.to_datetime(repeat_customers['first_order'])
        ).dt.days
        
        print(f"\n👥 FOUND {len(repeat_customers)} REPEAT CUSTOMERS (3+ orders)")
        
        # Top spenders
        top_spenders = repeat_customers.nlargest(3, 'total_spent')
        print(f"\n💰 TOP SPENDERS:")
        for i, customer in top_spenders.iterrows():
            print(f"   Customer from {customer['city']}, {customer['state']}")
            print(f"   • Total spent: ${customer['total_spent']:.2f}")
            print(f"   • Orders: {customer['total_orders']}")
            print(f"   • Days attended: {customer['days_attended']}")
            print(f"   • Customer lifetime: {customer['customer_lifetime_days']} days")
            print()
        
        # Most frequent attendees
        most_frequent = repeat_customers.nlargest(3, 'total_orders')
        print(f"\n🎭 MOST FREQUENT ATTENDEES:")
        for i, customer in most_frequent.iterrows():
            print(f"   Customer from {customer['city']}, {customer['state']}")
            print(f"   • Total orders: {customer['total_orders']}")
            print(f"   • Total spent: ${customer['total_spent']:.2f}")
            print(f"   • Days variety: {customer['days_variety']} different days")
            print(f"   • Avg order value: ${customer['avg_order_value']:.2f}")
            print()
        
        # Most diverse attendance
        most_diverse = repeat_customers.nlargest(3, 'days_variety')
        print(f"\n🌟 MOST DIVERSE ATTENDANCE:")
        for i, customer in most_diverse.iterrows():
            print(f"   Customer from {customer['city']}, {customer['state']}")
            print(f"   • Attends {customer['days_variety']} different days: {customer['days_attended']}")
            print(f"   • Total orders: {customer['total_orders']}")
            print(f"   • Total spent: ${customer['total_spent']:.2f}")
            print()
    
    def controllable_variables_analysis(self):
        """Analyze variables that showrunners can control"""
        print("\n" + "="*60)
        print("CONTROLLABLE VARIABLES FOR SHOWRUNNERS")
        print("="*60)
        
        # 1. Day of week performance
        day_performance = self.df.groupby('day_of_week').agg({
            'Order ID': 'count',
            'Gross sales': 'sum',
            'Event start date': 'nunique'
        }).reset_index()
        day_performance['avg_orders_per_show'] = day_performance['Order ID'] / day_performance['Event start date']
        day_performance['avg_revenue_per_show'] = day_performance['Gross sales'] / day_performance['Event start date']
        
        print(f"\n🗓️ DAY OF WEEK PERFORMANCE:")
        day_performance_sorted = day_performance.sort_values('avg_orders_per_show', ascending=False)
        for _, day in day_performance_sorted.iterrows():
            print(f"   {day['day_of_week']}: {day['avg_orders_per_show']:.1f} avg orders/show, ${day['avg_revenue_per_show']:.2f} avg revenue/show")
        
        # 2. Pricing strategy impact
        pricing_impact = self.df.groupby('Payment type').agg({
            'Order ID': 'count',
            'Gross sales': 'sum'
        }).reset_index()
        
        print(f"\n💰 PRICING STRATEGY IMPACT:")
        total_orders = pricing_impact['Order ID'].sum()
        for _, payment in pricing_impact.iterrows():
            percentage = (payment['Order ID'] / total_orders) * 100
            avg_value = payment['Gross sales'] / payment['Order ID'] if payment['Order ID'] > 0 else 0
            print(f"   {payment['Payment type']}: {payment['Order ID']:,} orders ({percentage:.1f}%), avg ${avg_value:.2f}")
        
        # 3. Advance booking patterns
        booking_windows = pd.cut(self.df['days_before_event'], 
                               bins=[-1, 0, 1, 3, 7, 14, 30, float('inf')],
                               labels=['Same Day', '1 Day', '2-3 Days', '4-7 Days', '1-2 Weeks', '2-4 Weeks', '1+ Month'])
        
        booking_analysis = self.df.groupby(booking_windows).agg({
            'Order ID': 'count',
            'Gross sales': 'sum'
        }).reset_index()
        
        print(f"\n📅 BOOKING WINDOW ANALYSIS:")
        total_bookings = booking_analysis['Order ID'].sum()
        for _, window in booking_analysis.iterrows():
            percentage = (window['Order ID'] / total_bookings) * 100
            avg_value = window['Gross sales'] / window['Order ID'] if window['Order ID'] > 0 else 0
            print(f"   {window['days_before_event']}: {window['Order ID']:,} orders ({percentage:.1f}%), avg ${avg_value:.2f}")
        
        # 4. Customer acquisition vs retention
        customer_orders = self.df['customer_id'].value_counts()
        new_customers = len(customer_orders[customer_orders == 1])
        returning_customers = len(customer_orders[customer_orders > 1])
        
        new_revenue = self.df[self.df['customer_id'].isin(customer_orders[customer_orders == 1].index)]['Gross sales'].sum()
        returning_revenue = self.df[self.df['customer_id'].isin(customer_orders[customer_orders > 1].index)]['Gross sales'].sum()
        
        print(f"\n🔄 CUSTOMER ACQUISITION VS RETENTION:")
        print(f"   New customers: {new_customers:,} ({new_customers/(new_customers+returning_customers)*100:.1f}%)")
        print(f"   Returning customers: {returning_customers:,} ({returning_customers/(new_customers+returning_customers)*100:.1f}%)")
        print(f"   New customer revenue: ${new_revenue:,.2f} ({new_revenue/(new_revenue+returning_revenue)*100:.1f}%)")
        print(f"   Returning customer revenue: ${returning_revenue:,.2f} ({returning_revenue/(new_revenue+returning_revenue)*100:.1f}%)")
        
        return day_performance_sorted
    
    def generate_actionable_recommendations(self):
        """Generate specific recommendations for showrunners"""
        print("\n" + "="*60)
        print("ACTIONABLE RECOMMENDATIONS FOR SHOWRUNNERS")
        print("="*60)
        
        day_performance = self.controllable_variables_analysis()
        
        recommendations = []
        
        # Best day recommendation
        best_day = day_performance.iloc[0]['day_of_week']
        best_avg = day_performance.iloc[0]['avg_orders_per_show']
        recommendations.append(f"🗓️ SCHEDULING: Focus on {best_day} shows - they average {best_avg:.1f} orders per show")
        
        # Pricing recommendations
        free_orders = len(self.df[self.df['Payment type'] == 'Free'])
        total_orders = len(self.df)
        free_percentage = (free_orders / total_orders) * 100
        
        if free_percentage > 15:
            recommendations.append(f"💰 PRICING: {free_percentage:.1f}% of tickets are free - consider reducing to boost revenue")
        else:
            recommendations.append(f"💰 PRICING: Good balance with {free_percentage:.1f}% free tickets")
        
        # Booking window recommendations
        same_day = len(self.df[self.df['days_before_event'] == 0])
        same_day_pct = (same_day / total_orders) * 100
        
        if same_day_pct > 15:
            recommendations.append(f"📢 MARKETING: {same_day_pct:.1f}% are same-day purchases - promote earlier for better planning")
        
        # Customer retention
        repeat_customers = len(self.df['customer_id'].value_counts()[self.df['customer_id'].value_counts() > 1])
        total_customers = self.df['customer_id'].nunique()
        repeat_rate = (repeat_customers / total_customers) * 100
        
        recommendations.append(f"🔄 RETENTION: {repeat_rate:.1f}% repeat rate - implement loyalty programs to increase")
        
        # Geographic concentration
        dc_orders = len(self.df[self.df['Purchaser state'] == 'DC'])
        dc_percentage = (dc_orders / total_orders) * 100
        recommendations.append(f"🗺️ GEOGRAPHIC: {dc_percentage:.1f}% from DC - consider targeted marketing in MD/VA")
        
        print(f"\n🎯 TOP RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        return recommendations

def main():
    """Main analysis function"""
    print("Starting Show-Level Comedy Insights Analysis...")
    
    analyzer = ShowInsights()
    analyzer.load_data()
    
    # Run all analyses
    analyzer.analyze_individual_shows()
    analyzer.week_over_week_analysis()
    analyzer.repeat_customer_case_studies()
    analyzer.controllable_variables_analysis()
    analyzer.generate_actionable_recommendations()
    
    print(f"\n✅ Show-level analysis complete!")

if __name__ == "__main__":
    main()
