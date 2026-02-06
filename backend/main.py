from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
from collections import Counter
from datetime import datetime
import statistics

app = FastAPI(title="Report Analysis API")

# CORS middleware to allow Laravel frontend to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChartConfig(BaseModel):
    chart_type: str
    column: Optional[str] = None
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    group_column: Optional[str] = None
    series_column: Optional[str] = None
    aggregate: Optional[str] = None  # COUNT, SUM, AVG, MIN, MAX, MEDIAN, MODE, PERCENTAGE, DISTINCT_COUNT
    aggregate_column: Optional[str] = None  # Column to aggregate (or "all" for COUNT)
    title: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None

class ReportRequest(BaseModel):
    report_data: List[Dict[str, Any]]
    chart_configs: List[ChartConfig]

def aggregate_values(values: List[float], aggregate_type: str) -> float:
    """Aggregate a list of values based on aggregate type"""
    if not values:
        return 0
    
    aggregate_type = aggregate_type.upper() if aggregate_type else "COUNT"
    
    if aggregate_type == "COUNT":
        return len(values)
    elif aggregate_type == "DISTINCT_COUNT":
        return len(set(values))
    elif aggregate_type == "SUM":
        return sum(values)
    elif aggregate_type == "AVG" or aggregate_type == "MEAN":
        return sum(values) / len(values) if values else 0
    elif aggregate_type == "MIN":
        return min(values)
    elif aggregate_type == "MAX":
        return max(values)
    elif aggregate_type == "MEDIAN":
        return statistics.median(values) if values else 0
    elif aggregate_type == "MODE":
        try:
            return statistics.mode(values)
        except statistics.StatisticsError:
            # If no unique mode, return most common
            return Counter(values).most_common(1)[0][0] if values else 0
    elif aggregate_type == "PERCENTAGE":
        # For percentage, we need total - this will be handled in the calling function
        return sum(values)
    else:
        return len(values)  # Default to count

def analyze_data_for_chart(report_data: List[Dict], config: ChartConfig) -> Dict[str, Any]:
    """Analyze report data based on chart configuration"""
    
    chart_type = config.chart_type.lower()
    result = {
        "chart_type": chart_type,
        "title": config.title or f"{chart_type.title()} Chart",
        "x_label": config.x_label,
        "y_label": config.y_label,
        "data": {}
    }
    
    try:
        if chart_type in ["bar_chart", "pie_chart"]:
            # Bar/Pie chart with aggregation support
            if not config.column:
                raise ValueError(f"Column is required for {chart_type}")
            
            aggregate_type = (config.aggregate or "COUNT").upper()
            aggregate_column = config.aggregate_column
            
            # Group by column and aggregate
            grouped_data = {}
            for row in report_data:
                col_val = str(row.get(config.column, ""))
                if not col_val:
                    continue
                
                if aggregate_type == "COUNT" and (not aggregate_column or aggregate_column == "all"):
                    # Simple count of rows
                    if col_val not in grouped_data:
                        grouped_data[col_val] = []
                    grouped_data[col_val].append(1)  # Count each row
                elif aggregate_type == "DISTINCT_COUNT":
                    # Distinct count - can count distinct values of a specific column or all rows
                    if not aggregate_column or aggregate_column == "all":
                        # Count distinct rows (each row is unique) - use a unique identifier
                        if col_val not in grouped_data:
                            grouped_data[col_val] = []
                        # Use row index or a combination to make each row unique
                        row_id = str(id(row))  # Unique identifier for each row
                        grouped_data[col_val].append(row_id)
                    else:
                        # Count distinct values of a specific column
                        distinct_val = row.get(aggregate_column)
                        if distinct_val is not None:
                            distinct_val = str(distinct_val)
                            if col_val not in grouped_data:
                                grouped_data[col_val] = []
                            grouped_data[col_val].append(distinct_val)  # Store value for distinct counting
                else:
                    # Aggregate a specific column
                    agg_col = aggregate_column if aggregate_column and aggregate_column != "all" else None
                    if not agg_col:
                        # Default: count rows
                        if col_val not in grouped_data:
                            grouped_data[col_val] = []
                        grouped_data[col_val].append(1)
                    else:
                        agg_val = row.get(agg_col)
                        if agg_val is not None:
                            try:
                                agg_val = float(agg_val) if not isinstance(agg_val, (int, float)) else agg_val
                                if col_val not in grouped_data:
                                    grouped_data[col_val] = []
                                grouped_data[col_val].append(agg_val)
                            except (ValueError, TypeError):
                                pass
            
            # Calculate aggregates
            labels = []
            values = []
            total_for_percentage = 0
            
            for col_val in sorted(grouped_data.keys()):
                agg_result = aggregate_values(grouped_data[col_val], aggregate_type)
                labels.append(col_val)
                values.append(agg_result)
                if aggregate_type == "PERCENTAGE":
                    total_for_percentage += agg_result
            
            # Convert to percentage if needed
            if aggregate_type == "PERCENTAGE" and total_for_percentage > 0:
                values = [(v / total_for_percentage * 100) for v in values]
            
            result["data"] = {
                "labels": labels,
                "values": values
            }
            
        elif chart_type == "line_chart":
            # Line chart - can be raw data or aggregated
            if not config.x_column or not config.y_column:
                raise ValueError("x_column and y_column are required for line chart")
            
            # Check if aggregation is requested
            if config.aggregate:
                # Aggregated mode - group by x_column and aggregate y_column values
                aggregate_type = config.aggregate.upper()
                
                grouped_data = {}
                for row in report_data:
                    x_val = str(row.get(config.x_column, ""))
                    y_val = row.get(config.y_column)
                    
                    if x_val and y_val is not None:
                        try:
                            y_val = float(y_val) if not isinstance(y_val, (int, float)) else y_val
                            if x_val not in grouped_data:
                                grouped_data[x_val] = []
                            grouped_data[x_val].append(y_val)
                        except (ValueError, TypeError):
                            pass
                
                # Calculate aggregates for each x value
                aggregated_data = {}
                for x_val, y_values in grouped_data.items():
                    aggregated_data[x_val] = aggregate_values(y_values, aggregate_type)
                
                # Sort by x value if possible (try to convert to date/number)
                sorted_items = sorted(aggregated_data.items(), key=lambda x: try_convert_sort(x[0]))
                
                result["data"] = {
                    "labels": [item[0] for item in sorted_items],
                    "values": [item[1] for item in sorted_items]
                }
            else:
                # Raw data mode - plot all points without aggregation (like XY chart)
                points = []
                skipped_count = 0
                x_string_map = {}  # Map string x-values to numeric indices
                x_index = 0
                
                for row in report_data:
                    x_val = row.get(config.x_column)
                    y_val = row.get(config.y_column)
                    
                    if x_val is not None and y_val is not None:
                        try:
                            # Try to convert y to float
                            y_val = float(y_val) if not isinstance(y_val, (int, float)) else y_val
                            
                            # Try to convert x to float
                            try:
                                x_val = float(x_val) if not isinstance(x_val, (int, float)) else x_val
                            except (ValueError, TypeError):
                                # If x is a string, convert to numeric index
                                if isinstance(x_val, str):
                                    if x_val not in x_string_map:
                                        x_string_map[x_val] = x_index
                                        x_index += 1
                                    x_val = x_string_map[x_val]
                                else:
                                    skipped_count += 1
                                    continue
                            
                            points.append({"x": x_val, "y": y_val})
                        except (ValueError, TypeError):
                            skipped_count += 1
                            pass
                
                if skipped_count > 0 and len(points) == 0:
                    result["error"] = f"Could not convert x_column '{config.x_column}' and y_column '{config.y_column}' to numeric values."
                elif skipped_count > 0:
                    result["warning"] = f"Skipped {skipped_count} rows with non-numeric values"
                
                result["data"] = {
                    "points": points
                }
            
        elif chart_type == "xy_chart" or chart_type == "scatter_chart":
            # X-Y scatter chart
            if not config.x_column or not config.y_column:
                raise ValueError("x_column and y_column are required for xy chart")
            
            points = []
            skipped_count = 0
            x_string_map = {}  # Map string x-values to numeric indices
            x_index = 0
            
            for row in report_data:
                x_val = row.get(config.x_column)
                y_val = row.get(config.y_column)
                
                if x_val is not None and y_val is not None:
                    try:
                        # Try to convert y to float
                        y_val = float(y_val) if not isinstance(y_val, (int, float)) else y_val
                        
                        # Try to convert x to float
                        try:
                            x_val = float(x_val) if not isinstance(x_val, (int, float)) else x_val
                        except (ValueError, TypeError):
                            # If x is a string, convert to numeric index
                            if isinstance(x_val, str):
                                if x_val not in x_string_map:
                                    x_string_map[x_val] = x_index
                                    x_index += 1
                                x_val = x_string_map[x_val]
                            else:
                                skipped_count += 1
                                continue
                        
                        points.append({"x": x_val, "y": y_val})
                    except (ValueError, TypeError):
                        skipped_count += 1
                        pass
            
            if skipped_count > 0 and len(points) == 0:
                result["error"] = f"Could not convert x_column '{config.x_column}' and y_column '{config.y_column}' to numeric values. XY charts require numeric data."
            elif skipped_count > 0:
                result["warning"] = f"Skipped {skipped_count} rows with non-numeric values"
            
            result["data"] = {
                "points": points
            }
            
        elif chart_type == "grouped_bar_chart":
            # Grouped bar chart - group by group_column, series by series_column, with aggregation support
            if not config.group_column or not config.series_column:
                raise ValueError("group_column and series_column are required for grouped_bar_chart")
            
            aggregate_type = (config.aggregate or "COUNT").upper()
            aggregate_column = config.aggregate_column
            
            # Structure: {group_value: {series_value: [values]}}
            grouped_data = {}
            all_series_values = set()
            
            for row in report_data:
                group_val = str(row.get(config.group_column, ""))
                series_val = str(row.get(config.series_column, ""))
                
                if group_val and series_val:
                    all_series_values.add(series_val)
                    
                    if group_val not in grouped_data:
                        grouped_data[group_val] = {}
                    
                    if series_val not in grouped_data[group_val]:
                        grouped_data[group_val][series_val] = []
                    
                    # Collect values for aggregation
                    if aggregate_type == "COUNT" and (not aggregate_column or aggregate_column == "all"):
                        # Simple count of rows
                        grouped_data[group_val][series_val].append(1)
                    elif aggregate_type == "DISTINCT_COUNT":
                        # Distinct count - can count distinct values of a specific column or all rows
                        if not aggregate_column or aggregate_column == "all":
                            # Count distinct rows - use unique identifier
                            row_id = str(id(row))
                            grouped_data[group_val][series_val].append(row_id)
                        else:
                            # Count distinct values of a specific column
                            distinct_val = row.get(aggregate_column)
                            if distinct_val is not None:
                                distinct_val = str(distinct_val)
                                grouped_data[group_val][series_val].append(distinct_val)
                    else:
                        # Aggregate a specific column
                        agg_col = aggregate_column if aggregate_column and aggregate_column != "all" else None
                        if not agg_col:
                            # Default: count rows
                            grouped_data[group_val][series_val].append(1)
                        else:
                            agg_val = row.get(agg_col)
                            if agg_val is not None:
                                try:
                                    agg_val = float(agg_val) if not isinstance(agg_val, (int, float)) else agg_val
                                    grouped_data[group_val][series_val].append(agg_val)
                                except (ValueError, TypeError):
                                    pass
            
            # Sort series values for consistent ordering
            sorted_series = sorted(all_series_values)
            
            # Sort group values
            sorted_groups = sorted(grouped_data.keys())
            
            # Calculate aggregates for each group/series combination
            aggregated_data = {}
            for group_val in sorted_groups:
                aggregated_data[group_val] = {}
                for series_val in sorted_series:
                    if group_val in grouped_data and series_val in grouped_data[group_val]:
                        values = grouped_data[group_val][series_val]
                        aggregated_data[group_val][series_val] = aggregate_values(values, aggregate_type)
                    else:
                        aggregated_data[group_val][series_val] = 0
            
            # Create datasets for each series
            datasets = []
            colors = [
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
            ]
            
            for idx, series_val in enumerate(sorted_series):
                data = []
                for group_val in sorted_groups:
                    value = aggregated_data[group_val].get(series_val, 0)
                    data.append(value)
                
                datasets.append({
                    "label": series_val,
                    "data": data,
                    "backgroundColor": colors[idx % len(colors)]
                })
            
            result["data"] = {
                "labels": sorted_groups,
                "datasets": datasets
            }
            
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")
            
    except Exception as e:
        result["error"] = str(e)
    
    return result

def try_convert_sort(value: str):
    """Try to convert value for sorting (date, number, or string)"""
    # Try date format
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except:
        pass
    
    # Try number
    try:
        return float(value)
    except:
        pass
    
    # Return as string
    return value

@app.get("/api/analyze")
async def analyze_report(
    report_data: str = Query(..., description="JSON string of report data"),
    chart_configs: str = Query(..., description="JSON string of chart configurations")
):
    """
    Analyze report data and generate chart configurations
    
    Example:
    /api/analyze?report_data=[{...}]&chart_configs=[{"chart_type":"count_chart","column":"partyType","title":"Orders by Party Type"}]
    """
    try:
        # Parse JSON strings
        report_json = json.loads(report_data)
        configs_json = json.loads(chart_configs)
        
        # Validate and convert to models
        if not isinstance(report_json, list):
            raise ValueError("report_data must be an array")
        
        if not isinstance(configs_json, list):
            raise ValueError("chart_configs must be an array")
        
        chart_configs_list = [ChartConfig(**config) for config in configs_json]
        
        # Generate chart data for each configuration
        charts = []
        for config in chart_configs_list:
            chart_data = analyze_data_for_chart(report_json, config)
            charts.append(chart_data)
        
        return JSONResponse(content={
            "success": True,
            "charts": charts,
            "report_count": len(report_json)
        })
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_report_post(request: ReportRequest):
    """
    Analyze report data via POST request
    """
    try:
        charts = []
        for config in request.chart_configs:
            chart_data = analyze_data_for_chart(request.report_data, config)
            charts.append(chart_data)
        
        return JSONResponse(content={
            "success": True,
            "charts": charts,
            "report_count": len(request.report_data)
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Report Analysis API", "endpoints": ["/api/analyze"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

