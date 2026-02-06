# Testing Guide

## Quick Test

### Option 1: Use the Test HTML File
1. Open `test-report.html` in your browser
2. Click "Test with Sample Data" button
3. You'll be redirected to the charts page

### Option 2: Direct URL Test

Open this URL in your browser (with the data already encoded):

```
http://localhost:8000/report?report_data=[{"orderNo":"SALE-306","orderDate":"2026-01-31","partyName":"DISTRIBUTOR1260","partyType":"Distributor","fromPartyState":"Rajasthan","itemTotalAmt":82.95,"soTotalAmt":83.0,"orderStatus":"PENDING"},{"orderNo":"SALE-304","orderDate":"2026-01-27","partyName":"DISTRIBUTOR1260","partyType":"Distributor","fromPartyState":"Rajasthan","itemTotalAmt":82.95,"soTotalAmt":83.0,"orderStatus":"CONVERTED INTO INVOICE"},{"orderNo":"SALE-299","orderDate":"2026-01-24","partyName":"DISTRIBUTOR1260","partyType":"Distributor","fromPartyState":"Rajasthan","itemTotalAmt":798.0,"soTotalAmt":798.0,"orderStatus":"PENDING"}]&chart_configs=[{"chart_type":"count_chart","column":"partyType","title":"Orders by Party Type"},{"chart_type":"bar_chart","column":"orderStatus","title":"Orders by Status"}]
```

### Option 3: Test with cURL (PowerShell)

```powershell
$reportData = '[{"orderNo":"SALE-306","orderDate":"2026-01-31","partyType":"Distributor","orderStatus":"PENDING","soTotalAmt":83.0}]'
$chartConfigs = '[{"chart_type":"count_chart","column":"partyType","title":"Orders by Party Type"}]'
$url = "http://localhost:8000/report?report_data=$([System.Web.HttpUtility]::UrlEncode($reportData))&chart_configs=$([System.Web.HttpUtility]::UrlEncode($chartConfigs))"
Start-Process $url
```

### Option 4: Test Python API Directly

Test the Python backend directly:

```powershell
cd backend
python test_api.py
```

## Expected Results

After submitting a report, you should see:
- A dashboard page with multiple charts
- Charts based on your configurations:
  - Count/Bar charts for categorical data
  - Pie charts for distributions
  - Line charts for trends over time
  - XY/Scatter charts for relationships

## Troubleshooting

1. **No charts showing?**
   - Check browser console for errors
   - Verify Python API is running on port 8001
   - Check Laravel logs: `frontend/storage/logs/laravel.log`

2. **Connection error?**
   - Ensure Python backend is running: `cd backend && python main.py`
   - Check `PYTHON_API_URL` in `.env` file

3. **Charts not rendering?**
   - Check browser console for JavaScript errors
   - Verify Chart.js is loading (check Network tab)

## Test Data Format

Your report data should be a JSON array of objects, where each object represents a row:

```json
[
  {
    "column1": "value1",
    "column2": "value2",
    "numericColumn": 123.45
  }
]
```

Chart configurations should specify:
- `chart_type`: count_chart, bar_chart, pie_chart, line_chart, or xy_chart
- `column`: for count/bar/pie charts
- `x_column` and `y_column`: for line/xy charts
- `title`: chart title (optional, will auto-generate if not provided)

