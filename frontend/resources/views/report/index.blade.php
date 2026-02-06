<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Report Analysis</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
        }
        .info {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .error {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        code {
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Report Analysis API</h1>
        
        @if(session('error'))
            <div class="error">
                {{ session('error') }}
            </div>
        @endif

        <div class="info">
            <h3>Step 1: Submit Report Data</h3>
            <p>Paste your report data (JSON array) below and click "Analyze Columns":</p>
            
            <form id="reportForm" method="POST" action="{{ route('report.analyze') }}">
                @csrf
                <textarea id="reportData" name="report_data" rows="10" style="width: 100%; font-family: monospace; padding: 10px;" placeholder='[{"orderNo":"SALE-306","partyType":"Distributor",...}]' required></textarea>
                <br><br>
                <button type="submit" style="background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 4px; cursor: pointer; font-size: 16px;">Analyze Columns</button>
            </form>
        </div>
        
        <div class="error" id="errorMessage" style="display: none;"></div>

        <div class="info" id="apiInfo" style="display: none;">
            <h3>API Usage (Alternative):</h3>
            <p><strong>POST Request to:</strong> <code>{{ url('/report/configure') }}</code></p>
            <p>Send report data and chart configurations together.</p>
        </div>
    </div>
    
    <script>
        document.getElementById('reportForm').addEventListener('submit', function(e) {
            const reportData = document.getElementById('reportData').value.trim();
            const errorDiv = document.getElementById('errorMessage');
            
            if (!reportData) {
                e.preventDefault();
                errorDiv.textContent = 'Please enter report data';
                errorDiv.style.display = 'block';
                return false;
            }
            
            try {
                JSON.parse(reportData);
            } catch (err) {
                e.preventDefault();
                errorDiv.textContent = 'Invalid JSON: ' + err.message;
                errorDiv.style.display = 'block';
                return false;
            }
        });
    </script>
</body>
</html>

