# Report Analysis Application

An application that accepts report data via API and generates interactive charts based on column configurations.

## Architecture

- **Backend**: Python FastAPI (runs on port 8000)
- **Frontend**: Laravel PHP (serves the web interface)

## Setup Instructions

### Backend Setup (Python)

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
```

3. Activate virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Run the FastAPI server:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8001`

**Note**: To run on a different server or allow remote access, use:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

**Optional CORS Configuration**: Set environment variable to restrict which frontends can access:
```bash
export CORS_ORIGINS="http://your-frontend-server.com,http://localhost:8000"
# Or allow all (default):
export CORS_ORIGINS="*"
```

### Frontend Setup (Laravel)

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install PHP dependencies (if using Composer):
```bash
composer install
```

3. Copy environment file:
```bash
cp .env.example .env
```

4. Generate application key:
```bash
php artisan key:generate
```

5. Run Laravel development server:
```bash
php artisan serve
```

The frontend will be available at `http://localhost:8000`

**Note**: Make sure to set `PYTHON_API_URL` in your `.env` file:
- For local backend: `PYTHON_API_URL=http://localhost:8001`
- For remote backend: `PYTHON_API_URL=http://your-backend-server-ip:8001`
- For production: `PYTHON_API_URL=https://api.yourdomain.com`

After changing `.env`, clear config cache:
```bash
php artisan config:clear
php artisan cache:clear
```

## Quick Start

1. Start the Python backend:
```bash
cd backend
python main.py
```

2. Start the Laravel frontend (in a new terminal):
```bash
cd frontend
php artisan serve
```

3. Use the test HTML file (`test-report.html`) to test the application, or send a POST request:

**Using cURL:**
```bash
curl -X POST http://localhost:8000/report \
  -H "Content-Type: application/json" \
  -d '{"report_data":[...], "chart_configs":[...]}'
```

**Using JavaScript fetch:**
```javascript
fetch('http://localhost:8000/report', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        report_data: [...],
        chart_configs: [...]
    })
})
```

## Usage

### API Endpoint

Send a POST request to the Laravel frontend:
```
POST http://localhost:8000/report
```

**With JSON Body:**
```json
{
  "report_data": [...],
  "chart_configs": [...]
}
```

**Or with Form Data:**
```
report_data=[JSON string]&chart_configs=[JSON string]
```

The Laravel frontend will forward the request to the Python API and display the charts.

### Example Request

**Using JavaScript fetch (POST):**
```javascript
const reportData = [
  {
    "orderNo": "SALE-306",
    "orderDate": "2026-01-31",
    "partyName": "DISTRIBUTOR1260",
    "partyType": "Distributor",
    "itemTotalAmt": 82.95,
    "soTotalAmt": 83.0,
    "orderStatus": "PENDING"
  }
  // ... more records
];

const chartConfigs = [
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
  },
  {
    "chart_type": "grouped_bar_chart",
    "group_column": "partyType",
    "series_column": "orderStatus",
    "title": "Order Status by Party Type",
    "x_label": "Party Type",
    "y_label": "Count"
  }
];

// POST request
fetch('http://localhost:8000/report', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        report_data: reportData,
        chart_configs: chartConfigs
    })
})
.then(response => response.text())
.then(html => {
    // Handle the HTML response (charts page)
    document.open();
    document.write(html);
    document.close();
});
```

### Chart Types Supported

1. **count_chart** / **bar_chart**: Counts occurrences of values in a column
   - Required: `column`
   - Optional: `title`, `x_label`, `y_label`

2. **pie_chart**: Shows distribution as pie slices
   - Required: `column`
   - Optional: `title`

3. **line_chart**: Line graph showing trends over time or categories
   - Required: `x_column`, `y_column`
   - Optional: `title`, `x_label`, `y_label`

4. **xy_chart** / **scatter_chart**: Scatter plot showing relationship between two numeric columns
   - Required: `x_column`, `y_column`
   - Optional: `title`, `x_label`, `y_label`

5. **grouped_bar_chart**: Grouped bar chart showing counts grouped by two categorical columns
   - Required: `group_column` (X-axis grouping), `series_column` (bars within each group)
   - Optional: `title`, `x_label`, `y_label`
   - Aggregates data by COUNT: group_column → series_column → count
   - Example: Order Status by Party Type, Order Status by State, Party Type by State

### Auto-Generated Charts

If `chart_configs` is not provided, the system will automatically generate chart configurations based on common column patterns in your data.

## API Documentation

FastAPI provides automatic API documentation:
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## Project Structure

```
.
├── backend/
│   ├── main.py              # FastAPI application
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── app/
│   │   └── Http/
│   │       └── Controllers/
│   │           └── ReportController.php
│   ├── resources/
│   │   └── views/
│   │       └── report/
│   │           ├── index.blade.php
│   │           └── show.blade.php
│   └── routes/
│       └── web.php
└── README.md
```

## Notes

- The backend API must be running before using the frontend
- Chart configurations are flexible - you can specify any columns from your report data
- The frontend uses Chart.js for rendering interactive charts
- All charts are responsive and work on mobile devices

