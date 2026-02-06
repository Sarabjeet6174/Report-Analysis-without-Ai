<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class ReportController extends Controller
{
    private function getApiUrl()
    {
        return env('PYTHON_API_URL', 'http://localhost:8001') . '/api/analyze';
    }

    public function index()
    {
        return view('report.index');
    }

    public function analyze(Request $request)
    {
        // Receive report data and return available columns
        $reportData = null;
        
        // Check JSON body first
        $jsonContent = $request->getContent();
        if (!empty($jsonContent)) {
            $jsonData = json_decode($jsonContent, true);
            if (json_last_error() === JSON_ERROR_NONE && is_array($jsonData)) {
                $reportData = $jsonData['report_data'] ?? $jsonData['data'] ?? null;
            }
        }
        
        // If not found in JSON, try form data
        if (!$reportData) {
            $reportData = $request->input('report_data') ?? $request->input('data');
        }

        if (!$reportData) {
            return response()->json(['error' => 'Report data is required'], 400);
        }

        // Parse report data if it's a string
        if (is_string($reportData)) {
            $decoded = json_decode($reportData, true);
            if (json_last_error() === JSON_ERROR_NONE && is_array($decoded)) {
                $reportData = $decoded;
            }
        }

        // Validate report data is an array
        if (!is_array($reportData) || empty($reportData)) {
            return response()->json(['error' => 'Invalid report data format. Expected a JSON array.'], 400);
        }

        // Analyze columns
        $firstRow = $reportData[0] ?? [];
        if (!is_array($firstRow) || empty($firstRow)) {
            return response()->json(['error' => 'Invalid report data structure.'], 400);
        }

        $columns = array_keys($firstRow);
        $columnTypes = [];
        
        foreach ($columns as $col) {
            $sampleValue = $firstRow[$col] ?? null;
            $isNumeric = false;
            $isDate = false;
            
            if ($sampleValue !== null) {
                // Check if numeric
                if (is_numeric($sampleValue)) {
                    $isNumeric = true;
                } else {
                    // Check if date
                    if (is_string($sampleValue) && preg_match('/^\d{4}-\d{2}-\d{2}/', $sampleValue)) {
                        $isDate = true;
                    }
                }
            }
            
            $columnTypes[$col] = [
                'type' => $isNumeric ? 'numeric' : ($isDate ? 'date' : 'categorical'),
                'sample' => $sampleValue
            ];
        }

        // Store report data and column info in session for later use
        session([
            'report_data' => $reportData,
            'columns' => $columns,
            'column_types' => $columnTypes
        ]);

        // Redirect to configure page
        return view('report.configure', [
            'columns' => $columns,
            'columnTypes' => $columnTypes,
            'rowCount' => count($reportData)
        ]);
    }

    public function configure(Request $request)
    {
        // Get report data from session
        $reportData = session('report_data');
        
        if (!$reportData) {
            return redirect()->route('report.index')
                ->with('error', 'No report data found. Please submit report data first.');
        }

        // Get chart configurations from request
        $chartConfigs = $request->input('chart_configs');
        
        if (!$chartConfigs) {
            $chartConfigs = [];
        }

        if (is_string($chartConfigs)) {
            $chartConfigs = json_decode($chartConfigs, true);
        }

        if (!is_array($chartConfigs) || empty($chartConfigs)) {
            return redirect()->route('report.index')
                ->with('error', 'At least one chart configuration is required.');
        }

        try {
            // Call Python API using POST with JSON body
            $response = Http::withHeaders([
                'Content-Type' => 'application/json',
            ])->post($this->getApiUrl(), [
                'report_data' => $reportData,
                'chart_configs' => $chartConfigs
            ]);

            if ($response->successful()) {
                $data = $response->json();
                if (!is_array($data)) {
                    $data = [];
                }
                return view('report.show', [
                    'charts' => $data['charts'] ?? [],
                    'reportCount' => $data['report_count'] ?? 0
                ]);
            } else {
                $errorBody = $response->body();
                $errorJson = $response->json();
                $errorMessage = $errorJson['detail'] ?? $errorBody ?? 'Unknown error';
                Log::error('API Error Response: ' . $errorBody);
                return redirect()->back()
                    ->with('error', 'Failed to analyze report: ' . $errorMessage)
                    ->withInput();
            }
        } catch (\Exception $e) {
            Log::error('Report analysis error: ' . $e->getMessage());
            Log::error('Stack trace: ' . $e->getTraceAsString());
            return redirect()->back()
                ->with('error', 'Error connecting to analysis API: ' . $e->getMessage())
                ->withInput();
        }
    }

    public function show(Request $request)
    {
        // POST request only - check JSON body first, then form data
        $reportData = null;
        $chartConfigs = null;
        
        // Check JSON body first
        $jsonContent = $request->getContent();
        if (!empty($jsonContent)) {
            $jsonData = json_decode($jsonContent, true);
            if (json_last_error() === JSON_ERROR_NONE && is_array($jsonData)) {
                $reportData = $jsonData['report_data'] ?? $jsonData['data'] ?? null;
                $chartConfigs = $jsonData['chart_configs'] ?? null;
            }
        }
        
        // If not found in JSON, try form data
        if (!$reportData) {
            $reportData = $request->input('report_data') ?? $request->input('data');
            $chartConfigs = $request->input('chart_configs');
        }

        if (!$reportData) {
            return redirect()->route('report.index')
                ->with('error', 'Report data is required');
        }

        // Parse report data if it's a string
        if (is_string($reportData)) {
            $decoded = json_decode($reportData, true);
            if (json_last_error() === JSON_ERROR_NONE && is_array($decoded)) {
                $reportData = $decoded;
            }
        }

        // Validate report data is an array
        if (!is_array($reportData) || empty($reportData)) {
            return redirect()->route('report.index')
                ->with('error', 'Invalid report data format. Expected a JSON array.');
        }

        // If chart_configs not provided, create default configs based on common columns
        if (!$chartConfigs) {
            $chartConfigs = $this->generateDefaultChartConfigs($reportData);
        } elseif (is_string($chartConfigs)) {
            // Parse chart configs if it's a string
            $decoded = json_decode($chartConfigs, true);
            if (json_last_error() === JSON_ERROR_NONE && is_array($decoded)) {
                $chartConfigs = $decoded;
            }
        }

        // Ensure report_data is JSON string for API call
        if (is_array($reportData)) {
            $reportDataJson = json_encode($reportData);
        } else {
            $reportDataJson = $reportData;
        }

        // Ensure chart_configs is JSON string for API call
        if (is_array($chartConfigs)) {
            $chartConfigsJson = json_encode($chartConfigs);
        } else {
            $chartConfigsJson = $chartConfigs;
        }

        try {
            // Call Python API
            $response = Http::get($this->getApiUrl(), [
                'report_data' => $reportDataJson,
                'chart_configs' => $chartConfigsJson
            ]);

            if ($response->successful()) {
                $data = $response->json();
                if (!is_array($data)) {
                    $data = [];
                }
                return view('report.show', [
                    'charts' => $data['charts'] ?? [],
                    'reportCount' => $data['report_count'] ?? 0
                ]);
            } else {
                return redirect()->route('report.index')
                    ->with('error', 'Failed to analyze report: ' . $response->body());
            }
        } catch (\Exception $e) {
            Log::error('Report analysis error: ' . $e->getMessage());
            return redirect()->route('report.index')
                ->with('error', 'Error connecting to analysis API: ' . $e->getMessage());
        }
    }

    private function generateDefaultChartConfigs($reportData)
    {
        // Parse report data to detect columns
        $data = is_string($reportData) ? json_decode($reportData, true) : $reportData;
        
        if (empty($data) || !is_array($data) || !isset($data[0]) || !is_array($data[0])) {
            return [];
        }

        $firstRow = $data[0];
        if (!is_array($firstRow)) {
            return [];
        }
        $columns = array_keys($firstRow);
        
        $configs = [];

        // Common categorical columns for count/bar/pie charts
        $categoricalColumns = ['partyType', 'orderStatus', 'partyName', 'itemName', 'fromPartyState', 'toPartyState'];
        
        foreach ($categoricalColumns as $col) {
            if (isset($firstRow[$col])) {
                $configs[] = [
                    'chart_type' => 'count_chart',
                    'column' => $col,
                    'title' => 'Orders by ' . ucwords(str_replace(['_', '-'], ' ', $col))
                ];
            }
        }

        // Numeric columns for line/xy charts
        $numericColumns = ['itemTotalAmt', 'soTotalAmt', 'itemQty', 'itemRate'];
        foreach ($numericColumns as $col) {
            if (isset($firstRow[$col])) {
                // Try to find a date column for x-axis
                if (isset($firstRow['orderDate'])) {
                    $configs[] = [
                        'chart_type' => 'line_chart',
                        'x_column' => 'orderDate',
                        'y_column' => $col,
                        'title' => ucwords(str_replace(['_', '-'], ' ', $col)) . ' Over Time',
                        'x_label' => 'Date',
                        'y_label' => ucwords(str_replace(['_', '-'], ' ', $col))
                    ];
                }
            }
        }

        return $configs;
    }
}

