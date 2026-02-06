# Quick Start Guide

## Step 1: Start the Python Backend

Open a terminal and run:

```bash
cd backend
python main.py
```

Or if you're using a virtual environment:

```bash
cd backend
# Activate virtual environment (Windows)
venv\Scripts\activate

# Or (Linux/Mac)
source venv/bin/activate

# Then run
python main.py
```

The backend will start on **http://localhost:8001**

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8001
```

## Step 2: Start the Laravel Frontend

Open a **new terminal** (keep the backend running) and run:

```bash
cd frontend
php artisan serve
```

The frontend will start on **http://localhost:8000**

You should see:
```
Laravel development server started: http://127.0.0.1:8000
```

## Step 3: Test the Application

### Option 1: Use the Test HTML File

1. Open `test-report.html` in your browser
2. Click "Test with POST Request" button
3. You'll see the charts dashboard

### Option 2: Use cURL (Command Line)

```bash
curl -X POST http://localhost:8000/report \
  -H "Content-Type: application/json" \
  -d '{
    "report_data": [
      {
        "orderNo": "SALE-306",
        "orderDate": "2026-01-31",
        "partyType": "Distributor",
        "orderStatus": "PENDING",
        "soTotalAmt": 83.0
      }
    ],
    "chart_configs": [
      {
        "chart_type": "count_chart",
        "column": "partyType",
        "title": "Orders by Party Type"
      }
    ]
  }' \
  -o output.html
```

Then open `output.html` in your browser.

### Option 3: Use JavaScript (Browser Console)

Open browser console (F12) and run:

```javascript
fetch('http://localhost:8000/report', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        report_data: [
            {
                "orderNo": "SALE-306",
                "orderDate": "2026-01-31",
                "partyType": "Distributor",
                "orderStatus": "PENDING",
                "soTotalAmt": 83.0
            }
        ],
        chart_configs: [
            {
                "chart_type": "count_chart",
                "column": "partyType",
                "title": "Orders by Party Type"
            }
        ]
    })
})
.then(response => response.text())
.then(html => {
    document.open();
    document.write(html);
    document.close();
});
```

### Option 4: Use Postman or Similar Tool

1. Create a new POST request
2. URL: `http://localhost:8000/report`
3. Headers: `Content-Type: application/json`
4. Body (raw JSON):
```json
{
  "report_data": [...your data...],
  "chart_configs": [...your configs...]
}
```

## Troubleshooting

### Backend not starting?
- Make sure Python is installed: `python --version`
- Install dependencies: `pip install -r backend/requirements.txt`
- Check if port 8001 is available

### Frontend not starting?
- Make sure PHP is installed: `php --version`
- Install dependencies: `cd frontend && composer install`
- Create `.env` file: Copy from `ENV_SETUP.md` or run `php artisan key:generate`
- Check if port 8000 is available

### Connection error?
- Make sure both servers are running
- Check that Python backend is on port 8001
- Verify `PYTHON_API_URL=http://localhost:8001` in frontend `.env` file

### Charts not showing?
- Open browser console (F12) to check for errors
- Verify the Python backend is responding: Visit `http://localhost:8001/docs`
- Check Laravel logs: `frontend/storage/logs/laravel.log`

## Example: Full Workflow

1. **Terminal 1** (Backend):
   ```bash
   cd backend
   python main.py
   ```

2. **Terminal 2** (Frontend):
   ```bash
   cd frontend
   php artisan serve
   ```

3. **Browser**: Open `test-report.html` and click "Test with POST Request"

4. **Result**: You should see the charts dashboard with your data!

## Stopping the Servers

- Press `Ctrl+C` in each terminal to stop the servers

