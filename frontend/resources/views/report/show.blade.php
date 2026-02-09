<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Report Analysis - Charts</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
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
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        .charts-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            max-width: 1400px;
            margin: 0 auto;
        }
        .chart-card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .chart-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }
        .chart-title {
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
            margin-bottom: 20px;
            text-align: center;
            padding-bottom: 15px;
            border-bottom: 2px solid #667eea;
        }
        .chart-wrapper {
            position: relative;
            height: 400px;
            margin-top: 20px;
        }
        .no-data {
            text-align: center;
            color: #999;
            padding: 40px;
            font-style: italic;
        }
        @media (max-width: 768px) {
            .charts-container {
                grid-template-columns: 1fr;
            }
            .header h1 {
                font-size: 1.8em;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Report Analysis Dashboard</h1>
        <p>Total Records: {{ $reportCount }}</p>
    </div>

    <div class="charts-container">
        @forelse($charts as $index => $chart)
            <div class="chart-card">
                <div class="chart-title">{{ $chart['title'] ?? 'Chart ' . ($index + 1) }}</div>
                <div class="chart-wrapper">
                    @if(isset($chart['error']))
                        <div class="no-data">Error: {{ $chart['error'] }}</div>
                    @elseif(empty($chart['data']))
                        <div class="no-data">No data available</div>
                    @else
                        <canvas id="chart-{{ $index }}"></canvas>
                    @endif
                </div>
            </div>
        @empty
            <div class="chart-card">
                <div class="no-data">No charts to display</div>
            </div>
        @endforelse
    </div>

    <script>
        const charts = @json($charts);

        charts.forEach((chartData, index) => {
            if (chartData.error || !chartData.data) {
                return;
            }

            const canvas = document.getElementById(`chart-${index}`);
            if (!canvas) return;

            const ctx = canvas.getContext('2d');
            const chartType = chartData.chart_type.toLowerCase();
            const data = chartData.data;

            let config = {
                type: getChartJsType(chartType),
                data: {},
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                        },
                        title: {
                            display: false
                        }
                    }
                }
            };

            if (chartType === 'xy_chart' || chartType === 'scatter_chart') {
                // Scatter chart with colorful points
                const points = data.points || [];
                const isDateXAxis = data.x_is_date || false;
                const vibrantColors = [
                    'rgba(255, 99, 132, 0.8)',   // Pink/Red
                    'rgba(54, 162, 235, 0.8)',   // Blue
                    'rgba(255, 206, 86, 0.8)',   // Yellow
                    'rgba(75, 192, 192, 0.8)',   // Teal
                    'rgba(153, 102, 255, 0.8)',  // Purple
                    'rgba(255, 159, 64, 0.8)',   // Orange
                    'rgba(199, 199, 199, 0.8)',  // Gray
                    'rgba(83, 102, 255, 0.8)',   // Indigo
                    'rgba(255, 99, 255, 0.8)',   // Magenta
                    'rgba(99, 255, 132, 0.8)',   // Green
                    'rgba(255, 206, 86, 0.8)',   // Gold
                    'rgba(54, 162, 235, 0.8)'    // Sky Blue
                ];
                
                const borderColors = [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)',
                    'rgba(199, 199, 199, 1)',
                    'rgba(83, 102, 255, 1)',
                    'rgba(255, 99, 255, 1)',
                    'rgba(99, 255, 132, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(54, 162, 235, 1)'
                ];
                
                // Create arrays of colors for each point
                const pointBackgroundColors = points.map((point, index) => 
                    vibrantColors[index % vibrantColors.length]
                );
                const pointBorderColors = points.map((point, index) => 
                    borderColors[index % borderColors.length]
                );
                
                config.data = {
                    datasets: [{
                        label: chartData.title,
                        data: points,
                        backgroundColor: pointBackgroundColors,
                        borderColor: pointBorderColors,
                        pointRadius: 6,
                        pointHoverRadius: 8,
                        pointBorderWidth: 2
                    }]
                };
                
                // Configure scales based on whether x-axis is date
                if (isDateXAxis) {
                    config.options.scales = {
                        x: {
                            type: 'time',
                            time: {
                                unit: 'day',
                                displayFormats: {
                                    day: 'DD-MMM-YYYY'
                                },
                                tooltipFormat: 'DD-MMM-YYYY'
                            },
                            title: {
                                display: !!chartData.x_label,
                                text: chartData.x_label || 'X Axis'
                            }
                        },
                        y: {
                            title: {
                                display: !!chartData.y_label,
                                text: chartData.y_label || 'Y Axis'
                            }
                        }
                    };
                } else {
                    config.options.scales = {
                        x: {
                            title: {
                                display: !!chartData.x_label,
                                text: chartData.x_label || 'X Axis'
                            }
                        },
                        y: {
                            title: {
                                display: !!chartData.y_label,
                                text: chartData.y_label || 'Y Axis'
                            }
                        }
                    };
                }
            } else if (chartType === 'line_chart' && data.points) {
                // Line chart in raw data mode (no aggregation)
                config.data = {
                    datasets: [{
                        label: chartData.title,
                        data: data.points || [],
                        backgroundColor: 'rgba(102, 126, 234, 0.2)',
                        borderColor: 'rgba(102, 126, 234, 1)',
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        fill: true
                    }]
                };
                config.options.scales = {
                    x: {
                        title: {
                            display: !!chartData.x_label,
                            text: chartData.x_label || 'X Axis'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: !!chartData.y_label,
                            text: chartData.y_label || 'Y Axis'
                        }
                    }
                };
            } else if (chartType === 'grouped_bar_chart') {
                // Grouped bar chart
                config.type = 'bar';
                config.data = {
                    labels: data.labels || [],
                    datasets: data.datasets || []
                };
                config.options.scales = {
                    x: {
                        stacked: false,
                        title: {
                            display: !!chartData.x_label,
                            text: chartData.x_label || 'Group'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        stacked: false,
                        title: {
                            display: !!chartData.y_label,
                            text: chartData.y_label || 'Count'
                        }
                    }
                };
            } else {
                // Bar, Line, Pie, Count charts
                const colors = generateColors(data.labels?.length || data.values?.length || 10);
                
                if (chartType === 'pie_chart' || chartType === 'doughnut_chart') {
                    const pieValues = data.values || [];
                    const pieLabels = data.labels || [];
                    const total = pieValues.reduce((sum, val) => sum + val, 0);
                    
                    config.data = {
                        labels: pieLabels,
                        datasets: [{
                            data: pieValues,
                            backgroundColor: colors,
                            borderColor: colors.map(c => c.replace('0.6', '1')),
                            borderWidth: 2
                        }]
                    };
                    
                    // Custom tooltip to show value and percentage
                    config.options.plugins.tooltip = {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    };
                    
                    // Custom legend to show value and percentage
                    config.options.plugins.legend = {
                        display: true,
                        position: 'top',
                        labels: {
                            generateLabels: function(chart) {
                                const data = chart.data;
                                if (data.labels.length && data.datasets.length) {
                                    const dataset = data.datasets[0];
                                    const total = dataset.data.reduce((a, b) => a + b, 0);
                                    return data.labels.map((label, i) => {
                                        const value = dataset.data[i];
                                        const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                        return {
                                            text: `${label}: ${value} (${percentage}%)`,
                                            fillStyle: dataset.backgroundColor[i],
                                            strokeStyle: dataset.borderColor[i],
                                            lineWidth: dataset.borderWidth,
                                            hidden: false,
                                            index: i
                                        };
                                    });
                                }
                                return [];
                            }
                        }
                    };
                    
                    // Add custom plugin to show values directly on pie slices
                    config.plugins = config.plugins || [];
                    config.plugins.push({
                        id: 'pieValueLabels',
                        afterDatasetsDraw: function(chart) {
                            const ctx = chart.ctx;
                            chart.data.datasets.forEach((dataset, i) => {
                                const meta = chart.getDatasetMeta(i);
                                const total = dataset.data.reduce((a, b) => a + b, 0);
                                meta.data.forEach((element, index) => {
                                    const value = dataset.data[index];
                                    const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                    const position = element.tooltipPosition();
                                    ctx.save();
                                    ctx.textAlign = 'center';
                                    ctx.textBaseline = 'middle';
                                    ctx.fillStyle = '#fff';
                                    ctx.font = 'bold 13px Arial';
                                    ctx.strokeStyle = '#333';
                                    ctx.lineWidth = 2;
                                    // Draw value with stroke for better visibility
                                    ctx.strokeText(value, position.x, position.y - 6);
                                    ctx.fillText(value, position.x, position.y - 6);
                                    ctx.font = '11px Arial';
                                    ctx.strokeText('(' + percentage + '%)', position.x, position.y + 8);
                                    ctx.fillText('(' + percentage + '%)', position.x, position.y + 8);
                                    ctx.restore();
                                });
                            });
                        }
                    });
                } else {
                    // Handle bar charts and aggregated line charts
                    if (chartType === 'line_chart' && data.labels && data.values) {
                        // Aggregated line chart
                        config.data = {
                            labels: data.labels || [],
                            datasets: [{
                                label: chartData.y_label || 'Value',
                                data: data.values || [],
                                backgroundColor: 'rgba(102, 126, 234, 0.2)',
                                borderColor: 'rgba(102, 126, 234, 1)',
                                borderWidth: 2,
                                pointRadius: 4,
                                pointHoverRadius: 6,
                                fill: true
                            }]
                        };
                        config.options.scales = {
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: !!chartData.y_label,
                                    text: chartData.y_label || 'Y Axis'
                                }
                            },
                            x: {
                                title: {
                                    display: !!chartData.x_label,
                                    text: chartData.x_label || 'X Axis'
                                }
                            }
                        };
                    } else {
                        // Bar charts
                        config.data = {
                            labels: data.labels || [],
                            datasets: [{
                                label: chartData.y_label || 'Value',
                                data: data.values || [],
                                backgroundColor: chartType === 'bar_chart' || chartType === 'count_chart' 
                                    ? colors 
                                    : 'rgba(102, 126, 234, 0.6)',
                                borderColor: 'rgba(102, 126, 234, 1)',
                                borderWidth: 2
                            }]
                        };
                    }

                    if (chartType !== 'line_chart') {
                        config.options.scales = {
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: !!chartData.y_label,
                                    text: chartData.y_label || 'Value'
                                }
                            },
                            x: {
                                title: {
                                    display: !!chartData.x_label,
                                    text: chartData.x_label || 'Category'
                                }
                            }
                        };
                    }
                }
            }

            new Chart(ctx, config);
        });

        function getChartJsType(chartType) {
            const typeMap = {
                'count_chart': 'bar',
                'bar_chart': 'bar',
                'pie_chart': 'pie',
                'line_chart': 'line',
                'xy_chart': 'scatter',
                'scatter_chart': 'scatter'
            };
            return typeMap[chartType.toLowerCase()] || 'bar';
        }

        function generateColors(count) {
            const colors = [];
            const baseColors = [
                'rgba(102, 126, 234, 0.6)',
                'rgba(118, 75, 162, 0.6)',
                'rgba(255, 99, 132, 0.6)',
                'rgba(54, 162, 235, 0.6)',
                'rgba(255, 206, 86, 0.6)',
                'rgba(75, 192, 192, 0.6)',
                'rgba(153, 102, 255, 0.6)',
                'rgba(255, 159, 64, 0.6)',
                'rgba(199, 199, 199, 0.6)',
                'rgba(83, 102, 255, 0.6)'
            ];
            
            for (let i = 0; i < count; i++) {
                colors.push(baseColors[i % baseColors.length]);
            }
            return colors;
        }
    </script>
</body>
</html>

