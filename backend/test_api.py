"""
Test script for the Report Analysis API
Run this after starting the FastAPI server to test the endpoints
"""

import requests
import json

# Sample report data
report_data = [
    {
        "orderNo": "SALE-306",
        "orderDate": "2026-01-31",
        "partyName": "DISTRIBUTOR1260",
        "partyType": "Distributor",
        "fromPartyState": "Rajasthan",
        "toPartyName": "Fast Trade Technologies",
        "toPartyType": "Company",
        "toPartyState": "Puducherry",
        "itemName": "Batch Item",
        "itemRate": 79.0,
        "itemQty": 1,
        "orderUnit": "Ltr",
        "itemTotalAmt": 82.95,
        "soTotalAmt": 83.0,
        "orderStatus": "PENDING"
    },
    {
        "orderNo": "SALE-304",
        "orderDate": "2026-01-27",
        "partyName": "DISTRIBUTOR1260",
        "partyType": "Distributor",
        "fromPartyState": "Rajasthan",
        "toPartyName": "Fast Trade Technologies",
        "toPartyType": "Company",
        "toPartyState": "Puducherry",
        "itemName": "Batch Item",
        "itemRate": 79.0,
        "itemQty": 1,
        "orderUnit": "Ltr",
        "itemTotalAmt": 82.95,
        "soTotalAmt": 83.0,
        "orderStatus": "CONVERTED INTO INVOICE"
    },
    {
        "orderNo": "SALE-299",
        "orderDate": "2026-01-24",
        "partyName": "DISTRIBUTOR1260",
        "partyType": "Distributor",
        "fromPartyState": "Rajasthan",
        "toPartyName": "Fast Trade Technologies",
        "toPartyType": "Company",
        "toPartyState": "Puducherry",
        "itemName": "Cup of steel",
        "itemRate": 380.0,
        "itemQty": 2,
        "orderUnit": "PCS",
        "itemTotalAmt": 798.0,
        "soTotalAmt": 798.0,
        "orderStatus": "PENDING"
    }
]

# Chart configurations
chart_configs = [
    {
        "chart_type": "count_chart",
        "column": "partyType",
        "title": "Orders by Party Type"
    },
    {
        "chart_type": "bar_chart",
        "column": "orderStatus",
        "title": "Orders by Status"
    },
    {
        "chart_type": "pie_chart",
        "column": "fromPartyState",
        "title": "Orders by State"
    },
    {
        "chart_type": "line_chart",
        "x_column": "orderDate",
        "y_column": "soTotalAmt",
        "title": "Total Amount Over Time",
        "x_label": "Date",
        "y_label": "Total Amount"
    },
    {
        "chart_type": "xy_chart",
        "x_column": "itemQty",
        "y_column": "itemTotalAmt",
        "title": "Quantity vs Total Amount",
        "x_label": "Quantity",
        "y_label": "Total Amount"
    }
]

def test_get_endpoint():
    """Test GET endpoint with query parameters"""
    url = "http://localhost:8001/api/analyze"
    
    params = {
        "report_data": json.dumps(report_data),
        "chart_configs": json.dumps(chart_configs)
    }
    
    print("Testing GET endpoint...")
    print(f"URL: {url}")
    print(f"Report records: {len(report_data)}")
    print(f"Chart configs: {len(chart_configs)}")
    print("\nSending request...\n")
    
    try:
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Report Count: {data.get('report_count')}")
            print(f"Charts Generated: {len(data.get('charts', []))}")
            
            for i, chart in enumerate(data.get('charts', []), 1):
                print(f"\nChart {i}:")
                print(f"  Type: {chart.get('chart_type')}")
                print(f"  Title: {chart.get('title')}")
                if 'data' in chart:
                    if 'labels' in chart['data']:
                        print(f"  Labels: {len(chart['data']['labels'])} items")
                    if 'values' in chart['data']:
                        print(f"  Values: {len(chart['data']['values'])} items")
                    if 'points' in chart['data']:
                        print(f"  Points: {len(chart['data']['points'])} items")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API. Make sure the FastAPI server is running on port 8001")
    except Exception as e:
        print(f"Error: {str(e)}")

def test_post_endpoint():
    """Test POST endpoint with JSON body"""
    url = "http://localhost:8001/api/analyze"
    
    payload = {
        "report_data": report_data,
        "chart_configs": chart_configs
    }
    
    print("\n\nTesting POST endpoint...")
    print(f"URL: {url}")
    print("\nSending request...\n")
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Report Count: {data.get('report_count')}")
            print(f"Charts Generated: {len(data.get('charts', []))}")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API. Make sure the FastAPI server is running on port 8001")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    print("=" * 60)
    print("Report Analysis API Test Script")
    print("=" * 60)
    
    test_get_endpoint()
    test_post_endpoint()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

