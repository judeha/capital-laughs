#!/usr/bin/env python3
"""
Basic Comedy Ticket Sales Analysis
This script provides high-level analysis that can run with minimal dependencies.
"""

import csv
import os
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json

def load_csv_data(data_folder='src/data'):
    """Load all CSV files and combine them"""
    all_data = []
    csv_files = [f for f in os.listdir(data_folder) if f.endswith('.csv') and 'eda' not in f.lower()]
    
    for filename in csv_files:
        filepath = os.path.join(data_folder, filename)
        day_name = filename.replace('.csv', '')
        
        with open(filepath, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                row['day_of_week'] = day_name
                all_data.append(row)
        
        print(f"Loaded {sum(1 for _ in open(filepath)) - 1} records from {day_name}")
    
    print(f"Total records loaded: {len(all_data)}")
    return all_data

def analyze_data(data):
    """Perform basic analysis on the data"""
    results = {}
    
    # Basic metrics
    results['total_orders'] = len(data)
    results['total_tickets'] = sum(int(row.get('Ticket quantity', 0)) for row in data)
    results['total_revenue'] = sum(float(row.get('Gross sales', 0)) for row in data if row.get('Gross sales'))
    results['unique_customers'] = len(set(row.get('Buyer email', '').lower() for row in data if row.get('Buyer email')))
    
    # Time analysis
    order_dates = []
    event_dates = []
    days_before_event = []
    order_hours = []
    
    for row in data:
        try:
            order_date = datetime.strptime(row['Order date'], '%Y-%m-%d %H:%M:%S')
            event_date = datetime.strptime(row['Event start date'], '%Y-%m-%d')
            
            order_dates.append(order_date)
            event_dates.append(event_date)
            
            days_diff = (event_date - order_date).days
            days_before_event.append(days_diff)
            order_hours.append(order_date.hour)
        except (ValueError, KeyError):
            continue
    
    # Purchase timing analysis
    if days_before_event:
        results['avg_days_before_event'] = sum(days_before_event) / len(days_before_event)
        results['same_day_purchases'] = sum(1 for d in days_before_event if d == 0)
        results['last_minute_purchases'] = sum(1 for d in days_before_event if d <= 1)
        results['advance_purchases'] = sum(1 for d in days_before_event if d >= 7)
    
    # Hourly patterns
    hour_counts = Counter(order_hours)
    results['peak_hour'] = max(hour_counts, key=hour_counts.get) if hour_counts else None
    results['hourly_distribution'] = dict(hour_counts)
    
    # Day of week analysis
    day_counts = Counter(row['day_of_week'] for row in data)
    results['orders_by_day'] = dict(day_counts)
    
    # Customer analysis
    customer_orders = defaultdict(int)
    customer_spending = defaultdict(float)
    
    for row in data:
        email = row.get('Buyer email', '').lower()
        if email:
            customer_orders[email] += 1
            try:
                customer_spending[email] += float(row.get('Gross sales', 0))
            except (ValueError, TypeError):
                pass
    
    repeat_customers = sum(1 for count in customer_orders.values() if count > 1)
    results['repeat_customer_rate'] = (repeat_customers / len(customer_orders) * 100) if customer_orders else 0
    results['avg_orders_per_customer'] = sum(customer_orders.values()) / len(customer_orders) if customer_orders else 0
    
    # Geographic analysis
    state_counts = Counter(row.get('Purchaser state', 'Unknown') for row in data)
    city_counts = Counter(row.get('Purchaser city', 'Unknown') for row in data)
    
    results['top_states'] = dict(state_counts.most_common(10))
    results['top_cities'] = dict(city_counts.most_common(10))
    
    # Payment analysis
    payment_counts = Counter(row.get('Payment type', 'Unknown') for row in data)
    results['payment_methods'] = dict(payment_counts)
    
    # Ticket quantity analysis
    quantity_counts = Counter(int(row.get('Ticket quantity', 1)) for row in data if row.get('Ticket quantity'))
    results['ticket_quantities'] = dict(quantity_counts)
    
    return results

def print_analysis_results(results):
    """Print formatted analysis results"""
    print("\n" + "="*60)
    print("COMEDY TICKET SALES ANALYSIS RESULTS")
    print("="*60)
    
    print(f"\n📊 OVERVIEW:")
    print(f"   Total Orders: {results['total_orders']:,}")
    print(f"   Total Tickets Sold: {results['total_tickets']:,}")
    print(f"   Total Revenue: ${results['total_revenue']:,.2f}")
    print(f"   Unique Customers: {results['unique_customers']:,}")
    print(f"   Average Order Value: ${results['total_revenue']/results['total_orders']:.2f}")
    
    print(f"\n⏰ PURCHASE TIMING:")
    print(f"   Average Days Before Event: {results.get('avg_days_before_event', 0):.1f}")
    print(f"   Same Day Purchases: {results.get('same_day_purchases', 0):,} ({results.get('same_day_purchases', 0)/results['total_orders']*100:.1f}%)")
    print(f"   Last Minute (≤1 day): {results.get('last_minute_purchases', 0):,}")
    print(f"   Advance (≥7 days): {results.get('advance_purchases', 0):,}")
    
    if results.get('peak_hour') is not None:
        print(f"   Peak Purchase Hour: {results['peak_hour']}:00")
    
    print(f"\n👥 CUSTOMER INSIGHTS:")
    print(f"   Repeat Customer Rate: {results['repeat_customer_rate']:.1f}%")
    print(f"   Average Orders per Customer: {results['avg_orders_per_customer']:.1f}")
    
    print(f"\n📅 ORDERS BY DAY:")
    for day, count in sorted(results['orders_by_day'].items(), key=lambda x: x[1], reverse=True):
        print(f"   {day}: {count:,} orders")
    
    print(f"\n🗺️  TOP STATES:")
    for state, count in list(results['top_states'].items())[:5]:
        print(f"   {state}: {count:,} orders")
    
    print(f"\n🏙️  TOP CITIES:")
    for city, count in list(results['top_cities'].items())[:5]:
        print(f"   {city}: {count:,} orders")
    
    print(f"\n💳 PAYMENT METHODS:")
    for method, count in results['payment_methods'].items():
        print(f"   {method}: {count:,} orders ({count/results['total_orders']*100:.1f}%)")
    
    print(f"\n🎫 TICKET QUANTITIES:")
    for qty, count in sorted(results['ticket_quantities'].items()):
        print(f"   {qty} ticket(s): {count:,} orders")

def save_results_json(results, filename='analysis_results.json'):
    """Save results to JSON file"""
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to {filename}")

def main():
    """Main analysis function"""
    print("Starting Comedy Ticket Sales Analysis...")
    
    # Load data
    data = load_csv_data()
    
    if not data:
        print("No data found! Please check that CSV files exist in src/data/")
        return
    
    # Analyze data
    results = analyze_data(data)
    
    # Print results
    print_analysis_results(results)
    
    # Save results
    save_results_json(results)
    
    print(f"\n✅ Analysis complete!")
    print(f"📈 To view the interactive dashboard, run: streamlit run src/streamlit_app.py")

if __name__ == "__main__":
    main()
