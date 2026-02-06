<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Configure Charts - Report Analysis</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #667eea;
        }
        .header h1 {
            color: #333;
            font-size: 2em;
            margin-bottom: 10px;
        }
        .info-box {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .chart-config {
            background: #f5f5f5;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 2px solid #ddd;
        }
        .chart-config-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .chart-config h3 {
            color: #667eea;
            margin-bottom: 15px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #333;
        }
        .form-group select,
        .form-group input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin: 5px;
        }
        button:hover {
            background: #5568d3;
        }
        .btn-danger {
            background: #f44336;
        }
        .btn-danger:hover {
            background: #d32f2f;
        }
        .btn-success {
            background: #4caf50;
        }
        .btn-success:hover {
            background: #45a049;
        }
        #generateCharts {
            background: #4caf50;
            padding: 15px 30px;
            font-size: 18px;
            width: 100%;
            margin-top: 20px;
        }
        #generateCharts:hover {
            background: #45a049;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Configure Charts</h1>
            <p>Total Records: <span id="rowCount">0</span></p>
        </div>

        <div class="info-box">
            <strong>Available Columns:</strong>
            <div id="columnsList" style="margin-top: 10px;"></div>
        </div>

        <div id="chartsContainer">
            <div class="chart-config" data-chart-index="0">
                <div class="chart-config-header">
                    <h3>Chart 1</h3>
                    <button type="button" class="btn-danger" onclick="removeChart(0)">Remove</button>
                </div>
                <div class="form-group">
                    <label>Chart Type:</label>
                    <select name="chart_type" onchange="updateChartFields(0)">
                        <option value="bar_chart">Bar Chart</option>
                        <option value="pie_chart">Pie Chart</option>
                        <option value="line_chart">Line Chart</option>
                        <option value="xy_chart">XY/Scatter Chart</option>
                        <option value="grouped_bar_chart">Grouped Bar Chart</option>
                    </select>
                </div>
                <div id="chartFields0">
                    <!-- Dynamic fields based on chart type -->
                </div>
            </div>
        </div>

        <button type="button" onclick="addChart()" style="background: #2196F3;">+ Add Chart</button>
        
        <form id="configureForm" method="POST" action="{{ route('report.configure') }}">
            @csrf
            <input type="hidden" name="chart_configs" id="chartConfigsInput">
            <button type="submit" id="generateCharts">Generate Charts</button>
        </form>
        
        @if(session('error'))
            <div class="error" style="background: #ffebee; color: #c62828; padding: 15px; border-radius: 8px; margin-top: 20px;">
                <strong>Error:</strong> {{ session('error') }}
            </div>
        @endif
    </div>

    <script>
        let columns = @json($columns ?? []);
        let columnTypes = @json($columnTypes ?? []);
        let chartCount = 1;

        // Load columns on page load
        window.onload = function() {
            document.getElementById('rowCount').textContent = {{ $rowCount ?? 0 }};
            displayColumns();
            updateChartFields(0);
        };

        function displayColumns() {
            const columnsList = document.getElementById('columnsList');
            const categorical = columns.filter(c => columnTypes[c]?.type === 'categorical');
            const numeric = columns.filter(c => columnTypes[c]?.type === 'numeric');
            const date = columns.filter(c => columnTypes[c]?.type === 'date');
            
            let html = '';
            if (categorical.length > 0) {
                html += '<strong>Categorical:</strong> ' + categorical.join(', ') + '<br>';
            }
            if (numeric.length > 0) {
                html += '<strong>Numeric:</strong> ' + numeric.join(', ') + '<br>';
            }
            if (date.length > 0) {
                html += '<strong>Date:</strong> ' + date.join(', ') + '<br>';
            }
            columnsList.innerHTML = html;
        }

        function updateChartFields(index) {
            const chartConfig = document.querySelector(`[data-chart-index="${index}"]`);
            const chartType = chartConfig.querySelector('select[name="chart_type"]').value;
            const fieldsContainer = document.getElementById(`chartFields${index}`);
            
            let html = '';

            if (chartType === 'bar_chart' || chartType === 'pie_chart') {
                html += `
                    <div class="form-group">
                        <label>Group By (X-axis):</label>
                        <select name="column" required>
                            <option value="">Select column...</option>
                            ${columns.map(c => `<option value="${c}">${c}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Aggregate Function:</label>
                        <select name="aggregate" id="aggregateSelect${index}" required>
                            <option value="COUNT">COUNT</option>
                            <option value="DISTINCT_COUNT">DISTINCT COUNT</option>
                            <option value="SUM">SUM</option>
                            <option value="AVG">AVG (MEAN)</option>
                            <option value="MIN">MIN</option>
                            <option value="MAX">MAX</option>
                            <option value="MEDIAN">MEDIAN</option>
                            <option value="MODE">MODE</option>
                            <option value="PERCENTAGE">PERCENTAGE</option>
                        </select>
                    </div>
                    <div class="form-group" id="aggregateOf${index}">
                        <label>Aggregate Of (Y-axis Column):</label>
                        <select name="aggregate_column" id="aggregateColumn${index}">
                            <option value="all">All (for COUNT only)</option>
                            ${columns.map(c => `<option value="${c}">${c}</option>`).join('')}
                        </select>
                        <small style="color: #666; display: block; margin-top: 5px;">Select which column to aggregate (e.g., SUM of soTotalAmt, or DISTINCT COUNT of orderNo)</small>
                    </div>
                `;
            } else if (chartType === 'line_chart') {
                html += `
                    <div class="form-group">
                        <label>Chart Mode:</label>
                        <select name="line_mode" id="lineMode${index}" required>
                            <option value="raw">Raw Data (No Aggregation)</option>
                            <option value="aggregated">Aggregated</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>X-axis Column:</label>
                        <select name="x_column" required>
                            <option value="">Select column...</option>
                            ${columns.map(c => `<option value="${c}">${c}</option>`).join('')}
                        </select>
                    </div>
                    <div id="lineAggregateSection${index}" style="display: none;">
                        <div class="form-group">
                            <label>Aggregate Function:</label>
                            <select name="aggregate">
                                <option value="SUM">SUM</option>
                                <option value="AVG">AVG (MEAN)</option>
                                <option value="COUNT">COUNT</option>
                                <option value="MIN">MIN</option>
                                <option value="MAX">MAX</option>
                                <option value="MEDIAN">MEDIAN</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Y-axis Column:</label>
                        <select name="y_column" required>
                            <option value="">Select column...</option>
                            ${columns.map(c => `<option value="${c}">${c}</option>`).join('')}
                        </select>
                        <small style="color: #666; display: block; margin-top: 5px;" id="lineChartHelp${index}">Select Y-axis column (raw data points)</small>
                    </div>
                `;
            } else if (chartType === 'xy_chart') {
                html += `
                    <div class="form-group">
                        <label>X-axis Column:</label>
                        <select name="x_column" required>
                            <option value="">Select column...</option>
                            ${columns.map(c => `<option value="${c}">${c}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Y-axis Column:</label>
                        <select name="y_column" required>
                            <option value="">Select column...</option>
                            ${columns.filter(c => columnTypes[c]?.type === 'numeric').map(c => `<option value="${c}">${c}</option>`).join('')}
                        </select>
                    </div>
                `;
            } else if (chartType === 'grouped_bar_chart') {
                html += `
                    <div class="form-group">
                        <label>Group By (X-axis):</label>
                        <select name="group_column" required>
                            <option value="">Select column...</option>
                            ${columns.filter(c => columnTypes[c]?.type === 'categorical').map(c => `<option value="${c}">${c}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Series Column (Bars within each group):</label>
                        <select name="series_column" required>
                            <option value="">Select column...</option>
                            ${columns.filter(c => columnTypes[c]?.type === 'categorical').map(c => `<option value="${c}">${c}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Aggregate Function:</label>
                        <select name="aggregate" id="groupedAggregateSelect${index}" required>
                            <option value="COUNT">COUNT</option>
                            <option value="DISTINCT_COUNT">DISTINCT COUNT</option>
                            <option value="SUM">SUM</option>
                            <option value="AVG">AVG (MEAN)</option>
                            <option value="MIN">MIN</option>
                            <option value="MAX">MAX</option>
                            <option value="MEDIAN">MEDIAN</option>
                        </select>
                    </div>
                    <div class="form-group" id="groupedAggregateOf${index}">
                        <label>Aggregate Of (Y-axis Column):</label>
                        <select name="aggregate_column" id="groupedAggregateColumn${index}">
                            <option value="all">All (for COUNT only)</option>
                            ${columns.filter(c => columnTypes[c]?.type === 'numeric').map(c => `<option value="${c}">${c}</option>`).join('')}
                        </select>
                        <small style="color: #666; display: block; margin-top: 5px;">Select which numeric column to aggregate (e.g., SUM of soTotalAmt)</small>
                    </div>
                `;
            }

            // Common fields for all chart types
            html += `
                <div class="form-group">
                    <label>Title:</label>
                    <input type="text" name="title" placeholder="Chart title">
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>X-axis Label:</label>
                        <input type="text" name="x_label" placeholder="X-axis label">
                    </div>
                    <div class="form-group">
                        <label>Y-axis Label:</label>
                        <input type="text" name="y_label" placeholder="Y-axis label">
                    </div>
                </div>
            `;

            fieldsContainer.innerHTML = html;

            // Wait for DOM to update, then set up event listeners
            setTimeout(() => {
                // Add event listener for aggregate change (bar/pie charts)
                const aggregateSelect = fieldsContainer.querySelector('select[name="aggregate"]');
                if (aggregateSelect && (chartType === 'bar_chart' || chartType === 'pie_chart')) {
                    const aggregateOfDiv = document.getElementById(`aggregateOf${index}`);
                    // Set initial state
                    if (aggregateSelect.value === 'COUNT') {
                        if (aggregateOfDiv) {
                            aggregateOfDiv.style.display = 'none';
                            const aggColSelect = document.getElementById(`aggregateColumn${index}`);
                            if (aggColSelect) aggColSelect.value = 'all';
                        }
                    } else {
                        if (aggregateOfDiv) aggregateOfDiv.style.display = 'block';
                        // For non-COUNT, remove "All" option if it exists
                        const aggColSelect = document.getElementById(`aggregateColumn${index}`);
                        if (aggColSelect) {
                            const allOption = aggColSelect.querySelector('option[value="all"]');
                            if (allOption) allOption.remove();
                            // If current value is "all", reset to first numeric column
                            if (aggColSelect.value === 'all' || !aggColSelect.value) {
                                const numericOptions = aggColSelect.querySelectorAll('option');
                                if (numericOptions.length > 0) {
                                    aggColSelect.value = numericOptions[0].value;
                                }
                            }
                        }
                    }
                    
                    aggregateSelect.addEventListener('change', function() {
                        const aggColSelect = document.getElementById(`aggregateColumn${index}`);
                        if (this.value === 'COUNT') {
                            if (aggregateOfDiv) {
                                aggregateOfDiv.style.display = 'none';
                                if (aggColSelect) aggColSelect.value = 'all';
                            }
                        } else {
                            if (aggregateOfDiv) aggregateOfDiv.style.display = 'block';
                            // Remove "All (for COUNT only)" option and ensure a column is selected
                            if (aggColSelect) {
                                const allOption = aggColSelect.querySelector('option[value="all"]');
                                if (allOption) allOption.remove();
                                // If current value is "all", reset to first column
                                if (aggColSelect.value === 'all' || !aggColSelect.value) {
                                    const options = aggColSelect.querySelectorAll('option');
                                    if (options.length > 0) {
                                        aggColSelect.value = options[0].value;
                                    }
                                }
                            }
                        }
                        updateAutoFill(index, chartType);
                    });
                }
                
                // Add event listener for aggregate change (grouped bar charts)
                const groupedAggregateSelect = fieldsContainer.querySelector('select[name="aggregate"]');
                if (groupedAggregateSelect && chartType === 'grouped_bar_chart') {
                    const groupedAggregateOfDiv = document.getElementById(`groupedAggregateOf${index}`);
                    if (groupedAggregateSelect.value === 'COUNT') {
                        if (groupedAggregateOfDiv) {
                            groupedAggregateOfDiv.style.display = 'none';
                            const aggColSelect = document.getElementById(`groupedAggregateColumn${index}`);
                            if (aggColSelect) aggColSelect.value = 'all';
                        }
                    } else {
                        if (groupedAggregateOfDiv) groupedAggregateOfDiv.style.display = 'block';
                        // For non-COUNT, remove "All" option if it exists
                        const aggColSelect = document.getElementById(`groupedAggregateColumn${index}`);
                        if (aggColSelect) {
                            const allOption = aggColSelect.querySelector('option[value="all"]');
                            if (allOption) allOption.remove();
                            // If current value is "all", reset to first numeric column
                            if (aggColSelect.value === 'all' || !aggColSelect.value) {
                                const numericOptions = aggColSelect.querySelectorAll('option');
                                if (numericOptions.length > 0) {
                                    aggColSelect.value = numericOptions[0].value;
                                }
                            }
                        }
                    }
                    
                    groupedAggregateSelect.addEventListener('change', function() {
                        const aggColSelect = document.getElementById(`groupedAggregateColumn${index}`);
                        if (this.value === 'COUNT') {
                            if (groupedAggregateOfDiv) {
                                groupedAggregateOfDiv.style.display = 'none';
                                if (aggColSelect) aggColSelect.value = 'all';
                            }
                        } else {
                            if (groupedAggregateOfDiv) groupedAggregateOfDiv.style.display = 'block';
                            // Remove "All (for COUNT only)" option and ensure a numeric column is selected
                            if (aggColSelect) {
                                const allOption = aggColSelect.querySelector('option[value="all"]');
                                if (allOption) allOption.remove();
                                // If current value is "all", reset to first numeric column
                                if (aggColSelect.value === 'all' || !aggColSelect.value) {
                                    const numericOptions = aggColSelect.querySelectorAll('option');
                                    if (numericOptions.length > 0) {
                                        aggColSelect.value = numericOptions[0].value;
                                    }
                                }
                            }
                        }
                        updateAutoFill(index, chartType);
                    });
                }
                
                // Add event listener for line chart mode change
                if (chartType === 'line_chart') {
                    const lineModeSelect = fieldsContainer.querySelector('select[name="line_mode"]');
                    const lineAggregateSection = document.getElementById(`lineAggregateSection${index}`);
                    const lineChartHelp = document.getElementById(`lineChartHelp${index}`);
                    
                    if (lineModeSelect) {
                        // Set initial state
                        if (lineModeSelect.value === 'raw') {
                            if (lineAggregateSection) lineAggregateSection.style.display = 'none';
                            if (lineChartHelp) lineChartHelp.textContent = 'Select Y-axis column (raw data points)';
                        } else {
                            if (lineAggregateSection) lineAggregateSection.style.display = 'block';
                            if (lineChartHelp) lineChartHelp.textContent = 'Select which column to aggregate (e.g., SUM of soTotalAmt by orderDate)';
                        }
                        
                        lineModeSelect.addEventListener('change', function() {
                            if (this.value === 'raw') {
                                if (lineAggregateSection) lineAggregateSection.style.display = 'none';
                                if (lineChartHelp) lineChartHelp.textContent = 'Select Y-axis column (raw data points)';
                            } else {
                                if (lineAggregateSection) lineAggregateSection.style.display = 'block';
                                if (lineChartHelp) lineChartHelp.textContent = 'Select which column to aggregate (e.g., SUM of soTotalAmt by orderDate)';
                            }
                            updateAutoFill(index, chartType);
                        });
                    }
                }
                
                // Add event listeners for auto-fill
                setupAutoFill(index, chartType);
                // Initial auto-fill
                updateAutoFill(index, chartType);
            }, 0);
        }
        
        function setupAutoFill(index, chartType) {
            const chartEl = document.querySelector(`[data-chart-index="${index}"]`);
            if (!chartEl) return;
            
            if (chartType === 'bar_chart' || chartType === 'pie_chart') {
                const columnSelect = chartEl.querySelector('select[name="column"]');
                const aggregateSelect = chartEl.querySelector('select[name="aggregate"]');
                const aggregateColumnSelect = chartEl.querySelector('select[name="aggregate_column"]');
                
                [columnSelect, aggregateSelect, aggregateColumnSelect].forEach(select => {
                    if (select) {
                        select.addEventListener('change', () => updateAutoFill(index, chartType));
                    }
                });
            } else if (chartType === 'line_chart') {
                const lineModeSelect = chartEl.querySelector('select[name="line_mode"]');
                const xColumnSelect = chartEl.querySelector('select[name="x_column"]');
                const yColumnSelect = chartEl.querySelector('select[name="y_column"]');
                const aggregateSelect = chartEl.querySelector('select[name="aggregate"]');
                
                [lineModeSelect, xColumnSelect, yColumnSelect, aggregateSelect].forEach(select => {
                    if (select) {
                        select.addEventListener('change', () => updateAutoFill(index, chartType));
                    }
                });
            } else if (chartType === 'xy_chart') {
                const xColumnSelect = chartEl.querySelector('select[name="x_column"]');
                const yColumnSelect = chartEl.querySelector('select[name="y_column"]');
                
                [xColumnSelect, yColumnSelect].forEach(select => {
                    if (select) {
                        select.addEventListener('change', () => updateAutoFill(index, chartType));
                    }
                });
            } else if (chartType === 'grouped_bar_chart') {
                const groupColumnSelect = chartEl.querySelector('select[name="group_column"]');
                const seriesColumnSelect = chartEl.querySelector('select[name="series_column"]');
                const aggregateSelect = chartEl.querySelector('select[name="aggregate"]');
                const aggregateColumnSelect = chartEl.querySelector('select[name="aggregate_column"]');
                
                [groupColumnSelect, seriesColumnSelect, aggregateSelect, aggregateColumnSelect].forEach(select => {
                    if (select) {
                        select.addEventListener('change', () => updateAutoFill(index, chartType));
                    }
                });
            }
        }
        
        function updateAutoFill(index, chartType) {
            const chartEl = document.querySelector(`[data-chart-index="${index}"]`);
            if (!chartEl) return;
            
            const titleInput = chartEl.querySelector('input[name="title"]');
            const xLabelInput = chartEl.querySelector('input[name="x_label"]');
            const yLabelInput = chartEl.querySelector('input[name="y_label"]');
            
            if (chartType === 'bar_chart' || chartType === 'pie_chart') {
                const column = chartEl.querySelector('select[name="column"]')?.value;
                const aggregate = chartEl.querySelector('select[name="aggregate"]')?.value;
                const aggregateColumn = chartEl.querySelector('select[name="aggregate_column"]')?.value;
                
                if (column) {
                    if (xLabelInput && !xLabelInput.value) {
                        xLabelInput.value = column;
                    }
                    
                    if (aggregate && aggregateColumn && aggregateColumn !== 'all') {
                        const yLabel = aggregate + ' of ' + aggregateColumn;
                        if (yLabelInput && !yLabelInput.value) {
                            yLabelInput.value = yLabel;
                        }
                        if (titleInput && !titleInput.value) {
                            titleInput.value = column + ' vs ' + aggregateColumn;
                        }
                    } else if (aggregate === 'COUNT' || aggregate === 'DISTINCT_COUNT') {
                        if (yLabelInput && !yLabelInput.value) {
                            yLabelInput.value = 'Count';
                        }
                        if (titleInput && !titleInput.value) {
                            titleInput.value = aggregate + ' by ' + column;
                        }
                    }
                }
            } else if (chartType === 'line_chart') {
                const lineMode = chartEl.querySelector('select[name="line_mode"]')?.value;
                const xColumn = chartEl.querySelector('select[name="x_column"]')?.value;
                const yColumn = chartEl.querySelector('select[name="y_column"]')?.value;
                const aggregate = chartEl.querySelector('select[name="aggregate"]')?.value;
                
                if (xColumn && yColumn) {
                    if (xLabelInput && !xLabelInput.value) {
                        xLabelInput.value = xColumn;
                    }
                    if (yLabelInput && !yLabelInput.value) {
                        if (lineMode === 'aggregated' && aggregate) {
                            yLabelInput.value = aggregate + ' of ' + yColumn;
                        } else {
                            yLabelInput.value = yColumn;
                        }
                    }
                    if (titleInput && !titleInput.value) {
                        titleInput.value = xColumn + ' vs ' + yColumn;
                    }
                }
            } else if (chartType === 'xy_chart') {
                const xColumn = chartEl.querySelector('select[name="x_column"]')?.value;
                const yColumn = chartEl.querySelector('select[name="y_column"]')?.value;
                
                if (xColumn && yColumn) {
                    if (xLabelInput && !xLabelInput.value) {
                        xLabelInput.value = xColumn;
                    }
                    if (yLabelInput && !yLabelInput.value) {
                        yLabelInput.value = yColumn;
                    }
                    if (titleInput && !titleInput.value) {
                        titleInput.value = xColumn + ' vs ' + yColumn;
                    }
                }
            } else if (chartType === 'grouped_bar_chart') {
                const groupColumn = chartEl.querySelector('select[name="group_column"]')?.value;
                const seriesColumn = chartEl.querySelector('select[name="series_column"]')?.value;
                const aggregate = chartEl.querySelector('select[name="aggregate"]')?.value;
                const aggregateColumn = chartEl.querySelector('select[name="aggregate_column"]')?.value;
                
                if (groupColumn && seriesColumn) {
                    if (xLabelInput && !xLabelInput.value) {
                        xLabelInput.value = groupColumn;
                    }
                    if (aggregate && aggregateColumn && aggregateColumn !== 'all') {
                        if (yLabelInput && !yLabelInput.value) {
                            yLabelInput.value = aggregate + ' of ' + aggregateColumn;
                        }
                    } else if (aggregate === 'COUNT' || aggregate === 'DISTINCT_COUNT') {
                        if (yLabelInput && !yLabelInput.value) {
                            yLabelInput.value = 'Count';
                        }
                    }
                    if (titleInput && !titleInput.value) {
                        titleInput.value = seriesColumn + ' by ' + groupColumn;
                    }
                }
            }
        }

        function addChart() {
            const container = document.getElementById('chartsContainer');
            const newChart = document.createElement('div');
            newChart.className = 'chart-config';
            newChart.setAttribute('data-chart-index', chartCount);
            newChart.innerHTML = `
                <div class="chart-config-header">
                    <h3>Chart ${chartCount + 1}</h3>
                    <button type="button" class="btn-danger" onclick="removeChart(${chartCount})">Remove</button>
                </div>
                <div class="form-group">
                    <label>Chart Type:</label>
                    <select name="chart_type" onchange="updateChartFields(${chartCount})">
                        <option value="bar_chart">Bar Chart</option>
                        <option value="pie_chart">Pie Chart</option>
                        <option value="line_chart">Line Chart</option>
                        <option value="xy_chart">XY/Scatter Chart</option>
                        <option value="grouped_bar_chart">Grouped Bar Chart</option>
                    </select>
                </div>
                <div id="chartFields${chartCount}"></div>
            `;
            container.appendChild(newChart);
            updateChartFields(chartCount);
            chartCount++;
        }

        function removeChart(index) {
            const chart = document.querySelector(`[data-chart-index="${index}"]`);
            if (chart && document.querySelectorAll('.chart-config').length > 1) {
                chart.remove();
            } else {
                alert('At least one chart is required');
            }
        }

        document.getElementById('configureForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const chartConfigs = [];
            const chartElements = document.querySelectorAll('.chart-config');
            
            chartElements.forEach((chartEl, index) => {
                // Get form elements from the chart config div
                const chartType = chartEl.querySelector('select[name="chart_type"]')?.value;
                
                if (!chartType) {
                    return; // Skip if no chart type selected
                }
                
                const config = {
                    chart_type: chartType
                };

                if (chartType === 'bar_chart' || chartType === 'pie_chart') {
                    config.column = chartEl.querySelector('select[name="column"]')?.value || '';
                    config.aggregate = chartEl.querySelector('select[name="aggregate"]')?.value || '';
                    const aggregateColumn = chartEl.querySelector('select[name="aggregate_column"]')?.value || '';
                    if (aggregateColumn && aggregateColumn !== 'all') {
                        config.aggregate_column = aggregateColumn;
                    }
                } else if (chartType === 'line_chart') {
                    config.x_column = chartEl.querySelector('select[name="x_column"]')?.value || '';
                    config.y_column = chartEl.querySelector('select[name="y_column"]')?.value || '';
                    const lineMode = chartEl.querySelector('select[name="line_mode"]')?.value;
                    if (lineMode === 'aggregated') {
                        config.aggregate = chartEl.querySelector('select[name="aggregate"]')?.value || '';
                    }
                } else if (chartType === 'xy_chart') {
                    config.x_column = chartEl.querySelector('select[name="x_column"]')?.value || '';
                    config.y_column = chartEl.querySelector('select[name="y_column"]')?.value || '';
                } else if (chartType === 'grouped_bar_chart') {
                    config.group_column = chartEl.querySelector('select[name="group_column"]')?.value || '';
                    config.series_column = chartEl.querySelector('select[name="series_column"]')?.value || '';
                    config.aggregate = chartEl.querySelector('select[name="aggregate"]')?.value || '';
                    const aggregateColumn = chartEl.querySelector('select[name="aggregate_column"]')?.value || '';
                    if (aggregateColumn && aggregateColumn !== 'all') {
                        config.aggregate_column = aggregateColumn;
                    }
                }

                const titleInput = chartEl.querySelector('input[name="title"]');
                const xLabelInput = chartEl.querySelector('input[name="x_label"]');
                const yLabelInput = chartEl.querySelector('input[name="y_label"]');

                if (titleInput && titleInput.value) config.title = titleInput.value;
                if (xLabelInput && xLabelInput.value) config.x_label = xLabelInput.value;
                if (yLabelInput && yLabelInput.value) config.y_label = yLabelInput.value;

                chartConfigs.push(config);
            });

            if (chartConfigs.length === 0) {
                alert('Please configure at least one chart');
                return;
            }

            // Validate all required fields
            const errors = [];
            chartConfigs.forEach((config, index) => {
                if (config.chart_type === 'bar_chart' || config.chart_type === 'pie_chart') {
                    if (!config.column) errors.push(`Chart ${index + 1}: Group By column is required`);
                    if (!config.aggregate) errors.push(`Chart ${index + 1}: Aggregate function is required`);
                } else if (config.chart_type === 'line_chart') {
                    if (!config.x_column) errors.push(`Chart ${index + 1}: X-axis column is required`);
                    if (!config.y_column) errors.push(`Chart ${index + 1}: Y-axis column is required`);
                    if (!config.aggregate) errors.push(`Chart ${index + 1}: Aggregate function is required`);
                } else if (config.chart_type === 'xy_chart') {
                    if (!config.x_column) errors.push(`Chart ${index + 1}: X-axis column is required`);
                    if (!config.y_column) errors.push(`Chart ${index + 1}: Y-axis column is required`);
                } else if (config.chart_type === 'grouped_bar_chart') {
                    if (!config.group_column) errors.push(`Chart ${index + 1}: Group column is required`);
                    if (!config.series_column) errors.push(`Chart ${index + 1}: Series column is required`);
                    if (!config.aggregate) errors.push(`Chart ${index + 1}: Aggregate function is required`);
                }
            });
            
            if (errors.length > 0) {
                alert('Please fix the following errors:\n\n' + errors.join('\n'));
                return;
            }

            console.log('Submitting chart configs:', chartConfigs);
            document.getElementById('chartConfigsInput').value = JSON.stringify(chartConfigs);
            this.submit();
        });
    </script>
</body>
</html>

