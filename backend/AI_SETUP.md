# AI-Powered Chart Configuration Setup

## Overview

The `/api/analyze-ai` endpoint uses OpenAI to automatically generate chart configurations from report data based on business insights.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install the `openai` library along with other dependencies.

### 2. Set OpenAI API Key

You have two options:

#### Option 1: Create a `.env` file (Recommended)

Create a file named `.env` in the `backend` directory with:

```
OPENAI_API_KEY=your-api-key-here
```

The application will automatically load this file when it starts.

#### Option 2: Set Environment Variable

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="your-api-key-here"
```

**Windows (Command Prompt):**
```cmd
set OPENAI_API_KEY=your-api-key-here
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**Note:** If using environment variables, you need to set them in the same terminal session where you run the backend, or set them system-wide.

### 3. Get OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Create a new API key
4. Copy the key and set it as an environment variable

## Usage

### Endpoint

**POST** `/api/analyze-ai`

### Request Body

**Note:** Pass your FULL report data. Only the first 10 rows are sent to OpenAI for analysis (to reduce token usage), but the generated chart configurations are applied to your FULL dataset.

```json
{
  "report_data": [
    {
      "column1": "value1",
      "column2": 123,
      "column3": "2024-01-01"
    }
    // ... full dataset
  ]
}
```

### Response

**Returns chart data ready to plot** (points, labels, values, etc.) along with the chart configurations for reference.

```json
{
  "success": true,
  "charts": [
    {
      "chart_type": "xy_chart",
      "title": "Sales Over Time",
      "x_label": "Date",
      "y_label": "Amount",
      "data": {
        "points": [
          {"x": 1234567890, "y": 1000},
          {"x": 1234567900, "y": 2000}
        ],
        "x_is_date": true
      }
    },
    {
      "chart_type": "bar_chart",
      "title": "Orders by Party Type",
      "data": {
        "labels": ["Customer", "Vendor"],
        "values": [50, 30]
      }
    }
  ],
  "chart_configs": [
    {
      "chart_type": "bar_chart",
      "column": "partyType",
      "aggregate": "COUNT",
      "aggregate_column": "all",
      "title": "Orders by Party Type"
    }
  ],
  "report_count": 100
}
```

### How It Works

1. **You send:** Full report data
2. **AI analyzes:** Only first 10 rows (to save tokens)
3. **AI generates:** Chart configurations
4. **System applies:** Configs to FULL report data
5. **You receive:** Chart data ready to plot (points, labels, values, etc.)

## Best Practices Implemented

### 1. **JSON Mode for Structured Output**
- Uses `response_format={"type": "json_object"}` to ensure consistent JSON responses
- Reduces parsing errors and malformed responses

### 2. **Retry Logic with Exponential Backoff**
- Automatically retries on rate limits and transient errors
- Uses exponential backoff with jitter to avoid thundering herd
- Maximum 3 retries with increasing delays

### 3. **Lower Temperature for Consistency**
- Uses `temperature=0.3` for more deterministic, structured output
- Better for generating consistent chart configurations

### 4. **Data Sampling**
- Only sends first 10 rows to OpenAI to reduce token usage
- Analyzes column types from full data before sending to AI
- Significantly reduces API costs and improves response time

### 5. **Response Validation**
- Validates JSON structure before returning
- Checks required fields for each chart type
- Skips invalid configurations gracefully

### 6. **Error Handling**
- Graceful fallback if OpenAI library not installed
- Clear error messages for missing API key
- Handles rate limits and API errors appropriately

### 7. **System Prompts**
- Clear, detailed system prompt for consistent results
- Includes all chart types and aggregation functions
- Business-focused recommendations

## Cost Optimization

- Uses `gpt-4o-mini` model (cost-effective, can be changed to `gpt-4o` or `gpt-4`)
- Only sends first 10 rows to OpenAI (not full dataset)
- Limits response tokens to 2000
- Applies AI-generated configs to full dataset locally (no additional API calls)

## Model Selection

You can change the model in `main.py`:

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",  # Change to "gpt-4o" or "gpt-4" for better results
    ...
)
```

- `gpt-4o-mini`: Fastest, most cost-effective (recommended)
- `gpt-4o`: Better quality, moderate cost
- `gpt-4`: Best quality, higher cost

## Testing

Send your full report data - the endpoint handles everything:

```bash
curl -X POST http://localhost:8001/api/analyze-ai \
  -H "Content-Type: application/json" \
  -d '{
    "report_data": [
      {"partyType": "Customer", "amount": 1000, "date": "2024-01-01"},
      {"partyType": "Vendor", "amount": 2000, "date": "2024-01-02"},
      {"partyType": "Customer", "amount": 1500, "date": "2024-01-03"}
      // ... your full dataset
    ]
  }'
```

**What happens:**
1. First 10 rows sent to OpenAI for analysis
2. AI generates chart configurations
3. Configs applied to FULL dataset
4. Returns chart data ready to plot

**Response includes:**
- `charts`: Array of chart data (points for XY charts, labels/values for bar charts, etc.)
- `chart_configs`: The AI-generated configurations (for reference)

## Troubleshooting

### Error: "OpenAI library not available"
- Run: `pip install openai`

### Error: "OPENAI_API_KEY environment variable is not set"
- Set the environment variable as shown above

### Error: Rate limit exceeded
- The retry logic will handle this automatically
- If persistent, consider upgrading your OpenAI plan

### Error: Invalid JSON response
- Check OpenAI API status
- Try again (may be a transient error)
- Check that your API key is valid

