from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
from collections import Counter
from datetime import datetime
import statistics
import time
import random
import logging
import os

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, skip .env loading
    pass

# OpenAI import with graceful fallback
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI library not installed. AI features will be disabled.")

# Basic application logger
logger = logging.getLogger("report_analysis")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

app = FastAPI(title="Report Analysis API")

# CORS middleware to allow Laravel frontend to access the API
# Allow specific origins from environment variable, or allow all for development
cors_origins = os.getenv("CORS_ORIGINS", "*")
if cors_origins == "*":
    allow_origins = ["*"]
else:
    # Split comma-separated origins
    allow_origins = [origin.strip() for origin in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
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

class AIReportRequest(BaseModel):
    report_data: List[Dict[str, Any]]
    include_suggestions: bool = True
    report_prompt: Optional[str] = None

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
            # Check if it's aggregated mode (has column and aggregate) or raw mode (has x_column and y_column)
            if config.column and config.aggregate:
                # Aggregated mode - same structure as bar chart
                if not config.column:
                    raise ValueError("column is required for aggregated line chart")
                
                aggregate_type = (config.aggregate or "COUNT").upper()
                aggregate_column = config.aggregate_column
                
                grouped_data = {}
                for row in report_data:
                    col_val = str(row.get(config.column, ""))
                    
                    if col_val:
                        if col_val not in grouped_data:
                            grouped_data[col_val] = []
                        
                        if aggregate_type == "COUNT" and (not aggregate_column or aggregate_column == "all"):
                            grouped_data[col_val].append(1)
                        elif aggregate_type == "DISTINCT_COUNT":
                            agg_col = aggregate_column if aggregate_column and aggregate_column != "all" else None
                            if not agg_col:
                                grouped_data[col_val].append(1)
                            else:
                                distinct_val = row.get(agg_col)
                                if distinct_val is not None:
                                    grouped_data[col_val].append(str(distinct_val))
                        else:
                            agg_col = aggregate_column if aggregate_column and aggregate_column != "all" else None
                            if not agg_col:
                                grouped_data[col_val].append(1)
                            else:
                                agg_val = row.get(agg_col)
                                if agg_val is not None:
                                    try:
                                        agg_val = float(agg_val) if not isinstance(agg_val, (int, float)) else agg_val
                                        grouped_data[col_val].append(agg_val)
                                    except (ValueError, TypeError):
                                        pass
                
                # Calculate aggregates
                aggregated_data = {}
                for col_val, values in grouped_data.items():
                    aggregated_data[col_val] = aggregate_values(values, aggregate_type)
                
                # Sort by column value if possible (try to convert to date/number)
                sorted_items = sorted(aggregated_data.items(), key=lambda x: try_convert_sort(x[0]))
                
                result["data"] = {
                    "labels": [item[0] for item in sorted_items],
                    "values": [item[1] for item in sorted_items]
                }
            elif config.x_column and config.y_column:
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
                            
                            # Try to convert x to float or date
                            try:
                                x_val = float(x_val) if not isinstance(x_val, (int, float)) else x_val
                            except (ValueError, TypeError):
                                # Try to parse as date first
                                if isinstance(x_val, str):
                                    try:
                                        # Try common date formats
                                        date_obj = datetime.strptime(x_val, "%Y-%m-%d")
                                        x_val = date_obj.timestamp()  # Convert to timestamp
                                    except (ValueError, TypeError):
                                        try:
                                            date_obj = datetime.strptime(x_val, "%Y-%m-%d %H:%M:%S")
                                            x_val = date_obj.timestamp()
                                        except (ValueError, TypeError):
                                            # If not a date, convert to numeric index
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
            else:
                raise ValueError("For line chart, either provide column+aggregate (aggregated mode) or x_column+y_column (raw mode)")
            
        elif chart_type == "xy_chart" or chart_type == "scatter_chart":
            # X-Y scatter chart
            if not config.x_column or not config.y_column:
                raise ValueError("x_column and y_column are required for xy chart")
            
            points = []
            skipped_count = 0
            x_string_map = {}  # Map string x-values to numeric indices
            x_index = 0
            is_date_column = False
            date_format = None
            
            # Try to detect if x_column is a date column by checking first few rows
            date_formats_to_try = [
                ("%Y-%m-%d", "%Y-%m-%d"),
                ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"),
                ("%d-%b-%Y", "%d-%b-%Y"),  # 01-Feb-2026
                ("%d/%b/%Y", "%d/%b/%Y"),
                ("%d/%m/%Y", "%d/%m/%Y"),
                ("%m/%d/%Y", "%m/%d/%Y"),
            ]
            
            for row in report_data[:5]:  # Check first 5 rows
                x_val = row.get(config.x_column)
                if x_val and isinstance(x_val, str):
                    for fmt, fmt_name in date_formats_to_try:
                        try:
                            datetime.strptime(x_val, fmt)
                            is_date_column = True
                            date_format = fmt
                            break
                        except (ValueError, TypeError):
                            continue
                    if is_date_column:
                        break
            
            for row in report_data:
                x_val = row.get(config.x_column)
                y_val = row.get(config.y_column)
                
                if x_val is not None and y_val is not None:
                    try:
                        # Try to convert y to float
                        y_val = float(y_val) if not isinstance(y_val, (int, float)) else y_val
                        
                        # Try to convert x to float or date
                        try:
                            x_val = float(x_val) if not isinstance(x_val, (int, float)) else x_val
                        except (ValueError, TypeError):
                            # Try to parse as date first
                            if isinstance(x_val, str):
                                if is_date_column and date_format:
                                    try:
                                        date_obj = datetime.strptime(x_val, date_format)
                                        x_val = date_obj.timestamp() * 1000  # Convert to milliseconds for Chart.js
                                    except (ValueError, TypeError):
                                        # If date parsing fails, try other formats
                                        parsed = False
                                        for fmt, _ in date_formats_to_try:
                                            try:
                                                date_obj = datetime.strptime(x_val, fmt)
                                                x_val = date_obj.timestamp() * 1000
                                                parsed = True
                                                break
                                            except (ValueError, TypeError):
                                                continue
                                        if not parsed:
                                            # If not a date, convert to numeric index
                                            if x_val not in x_string_map:
                                                x_string_map[x_val] = x_index
                                                x_index += 1
                                            x_val = x_string_map[x_val]
                                else:
                                    # Try to parse as date anyway
                                    parsed = False
                                    for fmt, _ in date_formats_to_try:
                                        try:
                                            date_obj = datetime.strptime(x_val, fmt)
                                            x_val = date_obj.timestamp() * 1000
                                            is_date_column = True
                                            parsed = True
                                            break
                                        except (ValueError, TypeError):
                                            continue
                                    if not parsed:
                                        # If not a date, convert to numeric index
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
                "points": points,
                "x_is_date": is_date_column
            }
            
        elif chart_type == "grouped_bar_chart":
            # Grouped bar chart - group by group_column, series by series_column, with aggregation support
            if not config.group_column or not config.series_column:
                raise ValueError("group_column and series_column are required for grouped_bar_chart")
            
            aggregate_type = (config.aggregate or "COUNT").upper()
            aggregate_column = config.aggregate_column
            
            # Validate that aggregate_column is provided for numeric aggregations
            numeric_aggregations = ["SUM", "AVG", "MIN", "MAX", "MEDIAN", "MODE", "PERCENTAGE"]
            if aggregate_type in numeric_aggregations:
                if not aggregate_column or aggregate_column == "all":
                    raise ValueError(f"aggregate_column is required for {aggregate_type} aggregation in grouped_bar_chart")
                
                # Verify the column exists in the data
                if report_data and len(report_data) > 0:
                    first_row = report_data[0]
                    if aggregate_column not in first_row:
                        # Try case-insensitive match
                        matching_col = None
                        for col in first_row.keys():
                            if col.lower() == aggregate_column.lower():
                                matching_col = col
                                break
                        if matching_col:
                            aggregate_column = matching_col
                        else:
                            available_cols = ", ".join(list(first_row.keys())[:10])
                            raise ValueError(f"Column '{aggregate_column}' not found in data. Available columns: {available_cols}")
            
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
                        # Aggregate a specific column (SUM, AVG, MIN, MAX, etc.)
                        agg_col = aggregate_column if aggregate_column and aggregate_column != "all" else None
                        if not agg_col:
                            # This shouldn't happen due to validation above, but handle gracefully
                            raise ValueError(f"aggregate_column is required for {aggregate_type} aggregation")
                        else:
                            agg_val = row.get(agg_col)
                            if agg_val is not None:
                                try:
                                    agg_val = float(agg_val) if not isinstance(agg_val, (int, float)) else agg_val
                                    grouped_data[group_val][series_val].append(agg_val)
                                except (ValueError, TypeError):
                                    # Skip non-numeric values
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
                        if values:  # Only aggregate if there are values
                            aggregated_data[group_val][series_val] = aggregate_values(values, aggregate_type)
                        else:
                            aggregated_data[group_val][series_val] = 0
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

def analyze_columns(report_data: List[Dict]) -> Dict[str, Dict[str, Any]]:
    """Analyze columns in report data to determine types"""
    if not report_data or len(report_data) == 0:
        return {}
    
    first_row = report_data[0]
    columns = list(first_row.keys())
    column_types = {}
    
    # Sample multiple rows for better detection (up to 10 rows)
    sample_rows = report_data[:min(10, len(report_data))]
    
    date_formats_to_try = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%d-%b-%Y",  # 01-Feb-2026
        "%d/%b/%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
    ]
    
    date_keywords = ['date', 'time', 'created', 'updated', 'modified', 'timestamp']
    
    for col in columns:
        is_numeric = False
        is_date = False
        date_count = 0
        numeric_count = 0
        total_samples = 0
        
        # Check multiple sample values
        for row in sample_rows:
            sample_value = row.get(col)
            if sample_value is None or sample_value == '':
                continue
            total_samples += 1
            
            # Check if numeric
            try:
                float(sample_value)
                numeric_count += 1
            except (ValueError, TypeError):
                # Check if date
                if isinstance(sample_value, str):
                    matches_date = False
                    for fmt in date_formats_to_try:
                        try:
                            datetime.strptime(sample_value, fmt)
                            matches_date = True
                            break
                        except (ValueError, TypeError):
                            continue
                    
                    # Additional check: column name suggests date
                    if not matches_date:
                        col_lower = col.lower()
                        for keyword in date_keywords:
                            if keyword in col_lower:
                                try:
                                    datetime.strptime(sample_value, "%Y-%m-%d")
                                    matches_date = True
                                    break
                                except (ValueError, TypeError):
                                    pass
                    
                    if matches_date:
                        date_count += 1
        
        # Determine type based on majority of samples
        if total_samples > 0:
            numeric_ratio = numeric_count / total_samples
            date_ratio = date_count / total_samples
            
            if numeric_ratio > 0.5:
                is_numeric = True
            elif date_ratio > 0.5:
                is_date = True
            elif date_count > 0:
                # If at least one date found and column name suggests date
                col_lower = col.lower()
                for keyword in date_keywords:
                    if keyword in col_lower:
                        is_date = True
                        break
        
        column_types[col] = {
            'type': 'numeric' if is_numeric else ('date' if is_date else 'categorical'),
            'is_numeric': is_numeric,
            'is_date': is_date,
            'sample': first_row.get(col)
        }
    
    return column_types

def call_openai_with_retry(client: Any, messages: List[Dict], max_retries: int = 3, base_delay: float = 1.0) -> Any:
    """
    Call OpenAI API with exponential backoff retry logic
    
    Best practices:
    - Retry on rate limits and transient errors
    - Exponential backoff with jitter
    - Validate response structure
    """
    for attempt in range(max_retries):
        try:
            logger.info("Calling OpenAI (attempt %d/%d)...", attempt + 1, max_retries)
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini for cost efficiency, can be changed to gpt-4o or gpt-4
                messages=messages,
                temperature=0.3,  # Lower temperature for more consistent, structured output
                response_format={"type": "json_object"},  # Force JSON mode for structured output
                max_tokens=2000
            )
            
            # Extract and parse JSON response
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")
            
            parsed_response = json.loads(content)
            logger.info("OpenAI call succeeded on attempt %d", attempt + 1)
            return parsed_response
            
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse OpenAI JSON response on attempt %d: %s", attempt + 1, str(e))
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff with jitter
                time.sleep(delay)
                continue
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse OpenAI response as JSON: {str(e)}. Response: {content[:200]}"
            )
        except Exception as e:
            error_str = str(e).lower()
            logger.warning("OpenAI error on attempt %d: %s", attempt + 1, str(e))
            # Retry on rate limits and transient errors
            if any(keyword in error_str for keyword in ['rate limit', 'timeout', 'connection', '503', '429']):
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(delay)
                    continue
            raise HTTPException(
                status_code=500,
                detail=f"OpenAI API error: {str(e)}"
            )
    
    logger.error("Exhausted OpenAI retries without success")
    raise HTTPException(status_code=500, detail="Failed to get response from OpenAI after retries")

def generate_chart_configs_with_ai(report_data: List[Dict], report_prompt: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Use OpenAI to generate chart configurations based on report data from a business perspective
    
    Best practices implemented:
    1. JSON mode for structured output
    2. Retry logic with exponential backoff
    3. Sample data to reduce token usage
    4. Clear system prompt for consistent results
    5. Lower temperature for structured data
    6. Response validation
    """
    logger.info(
        "generate_chart_configs_with_ai: rows=%d, report_prompt=%r",
        len(report_data),
        report_prompt,
    )

    if not OPENAI_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="OpenAI library not available. Please install it with: pip install openai"
        )
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY environment variable is not set"
        )
    
    client = OpenAI(api_key=api_key)
    logger.info("OpenAI client created for chart config generation")
    
    # Analyze columns first (use full data for column analysis)
    column_types = analyze_columns(report_data)
    
    # Sample only first 10 rows for AI analysis to reduce token usage
    sample_size = min(10, len(report_data))
    sample_data = report_data[:sample_size]
    
    # Prepare column information
    columns_info = []
    for col, info in column_types.items():
        columns_info.append({
            "name": col,
            "type": info['type'],
            "sample_value": str(info['sample'])[:50] if info['sample'] is not None else None
        })
    
    # System prompt for consistent, business-focused chart recommendations
    system_prompt = """You are a business intelligence analyst expert at creating meaningful data visualizations. 
Your task is to analyze report data and suggest chart configurations that provide business insights.

Available chart types:
1. bar_chart - For comparing categories (requires: column, aggregate, aggregate_column, title)
2. pie_chart - For showing proportions (requires: column, aggregate, aggregate_column, title)
3. line_chart - For trends over time or categories (requires: column + aggregate OR x_column + y_column, title)
4. xy_chart / scatter_chart - For relationships between two numeric variables (requires: x_column, y_column, title)
5. grouped_bar_chart - For comparing multiple series within groups (requires: group_column, series_column, aggregate, aggregate_column, title)

Available aggregate functions:
- COUNT: Count of rows (aggregate_column can be "all" or omitted)
- DISTINCT_COUNT: Count of distinct values (aggregate_column can be "all" or a specific column)
- SUM: Sum of numeric column (aggregate_column required, must be numeric)
- AVG/MEAN: Average of numeric column (aggregate_column required, must be numeric)
- MIN: Minimum value (aggregate_column required, must be numeric)
- MAX: Maximum value (aggregate_column required, must be numeric)
- MEDIAN: Median value (aggregate_column required, must be numeric)
- MODE: Most common value (aggregate_column required)
- PERCENTAGE: Percentage distribution (aggregate_column required)

For line_chart:
- **Aggregated mode (PREFERRED for time-based trends)**: Use column + aggregate + aggregate_column
  - Use this for trends over time (e.g., "Sales over time", "Count by Date")
  - Example: {"chart_type": "line_chart", "column": "Date", "aggregate": "SUM", "aggregate_column": "TotalAmt", "title": "Total Sales Over Time"}
  - When showing trends over time, ALWAYS use aggregated mode with column (date column) + aggregate + aggregate_column
- **Raw data mode**: Use x_column + y_column (only for scatter-like relationships, not time trends)
  - Only use this for non-time-based relationships between two numeric variables
  - Example: {"chart_type": "line_chart", "x_column": "Price", "y_column": "Quantity", "title": "Price vs Quantity"}

IMPORTANT RULES:
- **For time-based line charts (trends over time)**: ALWAYS use aggregated mode with column (date) + aggregate + aggregate_column
- Only use numeric columns for SUM, AVG, MIN, MAX, MEDIAN aggregations
- Use categorical columns for COUNT, DISTINCT_COUNT
- For xy_chart/scatter_chart: x_column can be numeric or date, y_column must be numeric
- When you see date columns and want to show trends over time, use line_chart in aggregated mode
- **IMPORTANT: You can create multiple charts of the same type if it provides different business insights**
  - For example: Multiple bar charts showing different KPIs (Orders by Status, Orders by Party Type, etc.)
  - For example: Multiple line charts showing different metrics over time (Sales over time, Orders over time, etc.)
  - For example: Multiple pie charts showing different distributions
  - Focus on business value, not chart type variety
- Generate 3-9 chart configurations that provide meaningful business insights (can be same or different chart types)
- Make titles descriptive and business-focused
- Include appropriate x_label and y_label for clarity

Return ONLY a valid JSON object with this exact structure:
{
  "chart_configs": [
    {
      "chart_type": "bar_chart",
      "column": "column_name",
      "aggregate": "COUNT",
      "aggregate_column": "all",
      "title": "Descriptive Business Title",
      "x_label": "X Axis Label",
      "y_label": "Y Axis Label"
    },
    {
      "chart_type": "line_chart",
      "column": "Date",
      "aggregate": "SUM",
      "aggregate_column": "TotalAmt",
      "title": "Total Sales Over Time",
      "x_label": "Date",
      "y_label": "Total Amount"
    }
  ]
}

Note: For line_chart showing trends over time, use aggregated mode (column + aggregate + aggregate_column), NOT raw mode (x_column + y_column)."""

    # User prompt with data context (optionally guided by user-specified report focus)
    focus_text = (
        f"User requested report focus: {report_prompt}\\n\\n"
        if report_prompt
        else ""
    )
    user_prompt = f"""Please provide chart configurations for this report data based on business perspective.

Report has {len(report_data)} total rows (showing first {len(sample_data)} rows for analysis) with the following columns:
{json.dumps(columns_info, indent=2)}

Sample data (first {len(sample_data)} rows):
{json.dumps(sample_data, indent=2)}

Generate 3-9 chart configurations that would provide meaningful business insights. Consider:
- Key performance indicators (KPIs)
- Trends and patterns
- Comparisons and distributions
- Relationships between variables

**Important:** You can create multiple charts of the same type if they show different business insights. For example:
- Multiple bar charts for different categorical breakdowns (Orders by Status, Orders by Party Type, Orders by State)
- Multiple line charts for different metrics over time (Sales over time, Order count over time, Average order value over time)
- Multiple pie charts for different distributions

{focus_text}Focus on business value and insights, not on having one of each chart type. If multiple charts of the same type provide better insights, create them."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        # Call OpenAI with retry logic
        start_time = time.time()
        response = call_openai_with_retry(client, messages)
        logger.info(
            "generate_chart_configs_with_ai: OpenAI response received in %.2fs",
            time.time() - start_time,
        )
        
        # Validate response structure
        if not isinstance(response, dict):
            raise ValueError("Response is not a dictionary")
        
        chart_configs = response.get("chart_configs", [])
        if not isinstance(chart_configs, list):
            raise ValueError("chart_configs is not a list")
        
        if len(chart_configs) == 0:
            raise ValueError("No chart configurations returned")
        
        # Validate each config matches ChartConfig structure
        validated_configs = []
        for config in chart_configs:
            try:
                # Validate required fields based on chart type
                chart_type = config.get("chart_type", "").lower()
                
                if chart_type in ["bar_chart", "pie_chart"]:
                    if not config.get("column"):
                        continue  # Skip invalid configs
                elif chart_type in ["xy_chart", "scatter_chart"]:
                    if not config.get("x_column") or not config.get("y_column"):
                        continue
                elif chart_type == "line_chart":
                    # Can be either aggregated or raw mode
                    if not (config.get("column") or config.get("x_column")):
                        continue
                elif chart_type == "grouped_bar_chart":
                    if not config.get("group_column") or not config.get("series_column"):
                        continue
                else:
                    continue  # Skip unknown chart types
                
                # Ensure aggregate_column is set for COUNT if not specified
                if config.get("aggregate") == "COUNT" and not config.get("aggregate_column"):
                    config["aggregate_column"] = "all"
                
                validated_configs.append(config)
            except Exception as e:
                # Skip invalid configs, log but don't fail
                print(f"Warning: Skipping invalid chart config: {str(e)}")
                continue
        
        if len(validated_configs) == 0:
            raise ValueError("No valid chart configurations after validation")
        
        logger.info(
            "generate_chart_configs_with_ai: returning %d validated configs",
            len(validated_configs),
        )
        return validated_configs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in generate_chart_configs_with_ai: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error generating chart configurations with AI: {str(e)}"
        )


def generate_chart_configs_and_suggestions_with_ai(report_data: List[Dict], report_prompt: Optional[str] = None) -> Dict[str, Any]:
    """
    Single OpenAI call that returns BOTH:
    - chart_configs: list of chart configuration dicts
    - suggestions: structured business/data analysis object
    """
    logger.info(
        "generate_chart_configs_and_suggestions_with_ai: rows=%d, report_prompt=%r",
        len(report_data),
        report_prompt,
    )

    if not OPENAI_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="OpenAI library not available. Please install it with: pip install openai"
        )
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY environment variable is not set"
        )
    
    client = OpenAI(api_key=api_key)
    logger.info("OpenAI client created for chart configs + suggestions")
    
    # Analyze columns for chart configs
    column_types = analyze_columns(report_data) if report_data else {}
    
    # Sample rows for token control (use 20 rows as a middle ground for both tasks)
    sample_size = min(20, len(report_data))
    sample_data = report_data[:sample_size]
    
    # Prepare column information (for chart configs)
    columns_info = []
    for col, info in column_types.items():
        columns_info.append({
            "name": col,
            "type": info["type"],
            "sample_value": str(info["sample"])[:50] if info.get("sample") is not None else None,
        })
    
    # Combined system prompt: chart configs + business suggestions
    system_prompt = """You are both:
1) A business intelligence analyst expert at creating meaningful data visualizations.
2) A business and data analyst focused on extracting insights, risks, and opportunities.

Your task is to:
- Suggest chart configurations that provide strong business insights.
- Produce a structured business/data analysis summary with key observations, trends, issues, and recommendations.

=== CHART CONFIGURATIONS PART ===

Available chart types:
1. bar_chart - For comparing categories (requires: column, aggregate, aggregate_column, title)
2. pie_chart - For showing proportions (requires: column, aggregate, aggregate_column, title)
3. line_chart - For trends over time or categories (requires: column + aggregate OR x_column + y_column, title)
4. xy_chart / scatter_chart - For relationships between two numeric variables (requires: x_column, y_column, title)
5. grouped_bar_chart - For comparing multiple series within groups (requires: group_column, series_column, aggregate, aggregate_column, title)

Available aggregate functions:
- COUNT: Count of rows (aggregate_column can be "all" or omitted)
- DISTINCT_COUNT: Count of distinct values (aggregate_column can be "all" or a specific column)
- SUM: Sum of numeric column (aggregate_column required, must be numeric)
- AVG/MEAN: Average of numeric column (aggregate_column required, must be numeric)
- MIN: Minimum value (aggregate_column required, must be numeric)
- MAX: Maximum value (aggregate_column required, must be numeric)
- MEDIAN: Median value (aggregate_column required, must be numeric)
- MODE: Most common value (aggregate_column required)
- PERCENTAGE: Percentage distribution (aggregate_column required)

For line_chart:
- Aggregated mode (PREFERRED for time-based trends): Use column + aggregate + aggregate_column
  - Use this for trends over time (e.g., "Sales over time", "Count by Date")
- Raw data mode: Use x_column + y_column (only for scatter-like relationships, not time trends)

IMPORTANT RULES FOR CHARTS:
- For time-based line charts (trends over time): ALWAYS use aggregated mode with column (date) + aggregate + aggregate_column.
- Only use numeric columns for SUM, AVG, MIN, MAX, MEDIAN aggregations.
- Use categorical columns for COUNT, DISTINCT_COUNT.
- For xy_chart/scatter_chart: x_column can be numeric or date, y_column must be numeric.
- You can create multiple charts of the same type if they provide different business insights (e.g., multiple bar charts for different categorical breakdowns).
- Generate 5–9 chart configurations that provide meaningful business insights.
- Make titles descriptive and business-focused, and include x_label and y_label where helpful.

The chart configurations MUST be returned under the key "chart_configs" as:
{
  "chart_configs": [
    {
      "chart_type": "bar_chart",
      "column": "column_name",
      "aggregate": "COUNT",
      "aggregate_column": "all",
      "title": "Descriptive Business Title",
      "x_label": "X Axis Label",
      "y_label": "Y Axis Label"
    }
  ],
  ...
}

=== BUSINESS/DATA ANALYSIS SUGGESTIONS PART ===

You are also a business and data analyst.

Analyze the provided report data carefully and produce meaningful insights. 
Your goal is to identify trends, anomalies, risks, and opportunities in the data.

Steps to follow:
1. Understand the structure of the report and key fields such as revenue, costs, quantities, customer data, product data, dates, and other metrics.
2. Identify patterns and trends in the data (growth, decline, seasonality, unusual spikes).
3. Highlight important metrics such as totals, averages, ratios, and comparisons where relevant.
4. Detect any anomalies, inconsistencies, or possible data quality issues.
5. Provide business insights explaining what the data suggests about performance.
6. Suggest actionable recommendations based on the analysis.
7. Mention potential risks or areas that require attention.
8. If useful, propose additional metrics or visualizations that could help understand the data better.

The suggestions MUST be returned under the key "suggestions" with this exact shape:
{
  "suggestions": {
    "summary": "Summary of the report",
    "key_observations": ["...", "..."],
    "important_trends": ["...", "..."],
    "detected_issues": ["...", "..."],
    "business_insights": ["...", "..."],
    "recommendations": ["...", "..."],
    "suggested_charts": ["...", "..."]
  }
}

=== FINAL OUTPUT FORMAT (CRITICAL) ===

Return ONLY a single valid JSON object with this exact top-level structure:
{
  "chart_configs": [ ... ],   // list of chart configuration objects
  "suggestions": {
    "summary": "Summary of the report",
    "key_observations": ["...", "..."],
    "important_trends": ["...", "..."],
    "detected_issues": ["...", "..."],
    "business_insights": ["...", "..."],
    "recommendations": ["...", "..."],
    "suggested_charts": ["...", "..."]
  }
}

Do not include any explanatory text outside of this JSON object."""

    focus_text = (
        f"User requested report focus: {report_prompt}\\n\\n"
        if report_prompt
        else ""
    )
    user_prompt = f"""We have tabular report data.

Total rows in report: {len(report_data)}.
Showing first {len(sample_data)} rows for analysis to stay within token limits.

Column information (for chart design):
{json.dumps(columns_info, indent=2)}

Sample data (first {len(sample_data)} rows):
{json.dumps(sample_data, indent=2)}

Using this data, please:
1) Propose 3–9 business-meaningful chart configurations under "chart_configs".
2) Provide structured business/data analysis under "suggestions" following the exact JSON shape specified in the system message.

{focus_text}Respond ONLY with a valid JSON object with "chart_configs" and "suggestions" at the top level."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    try:
        start_time = time.time()
        response = call_openai_with_retry(client, messages)
        logger.info(
            "generate_chart_configs_and_suggestions_with_ai: OpenAI response received in %.2fs",
            time.time() - start_time,
        )
        if not isinstance(response, dict):
            raise ValueError("AI response is not a JSON object")
        
        # Extract and validate chart configs
        chart_configs = response.get("chart_configs", [])
        if not isinstance(chart_configs, list):
            raise ValueError("chart_configs is not a list")
        
        if len(chart_configs) == 0:
            raise ValueError("No chart configurations returned")
        
        validated_configs: List[Dict[str, Any]] = []
        for config in chart_configs:
            try:
                chart_type = str(config.get("chart_type", "")).lower()
                
                if chart_type in ["bar_chart", "pie_chart"]:
                    if not config.get("column"):
                        continue
                elif chart_type in ["xy_chart", "scatter_chart"]:
                    if not config.get("x_column") or not config.get("y_column"):
                        continue
                elif chart_type == "line_chart":
                    if not (config.get("column") or config.get("x_column")):
                        continue
                elif chart_type == "grouped_bar_chart":
                    if not config.get("group_column") or not config.get("series_column"):
                        continue
                else:
                    continue
                
                # Ensure aggregate_column is set for COUNT if not specified
                if config.get("aggregate") == "COUNT" and not config.get("aggregate_column"):
                    config["aggregate_column"] = "all"
                
                validated_configs.append(config)
            except Exception as e:
                print(f"Warning: Skipping invalid chart config in combined AI call: {str(e)}")
                continue
        
        if len(validated_configs) == 0:
            raise ValueError("No valid chart configurations after validation")
        
        logger.info(
            "generate_chart_configs_and_suggestions_with_ai: %d validated configs",
            len(validated_configs),
        )

        # Extract and normalize suggestions
        raw_suggestions = response.get("suggestions", {})
        if not isinstance(raw_suggestions, dict):
            raw_suggestions = {}
        
        suggestions = {
            "summary": raw_suggestions.get("summary", ""),
            "key_observations": raw_suggestions.get("key_observations", []),
            "important_trends": raw_suggestions.get("important_trends", []),
            "detected_issues": raw_suggestions.get("detected_issues", []),
            "business_insights": raw_suggestions.get("business_insights", []),
            "recommendations": raw_suggestions.get("recommendations", []),
            "suggested_charts": raw_suggestions.get("suggested_charts", []),
        }
        
        for key in [
            "key_observations",
            "important_trends",
            "detected_issues",
            "business_insights",
            "recommendations",
            "suggested_charts",
        ]:
            value = suggestions.get(key, [])
            if isinstance(value, list):
                suggestions[key] = [str(item) for item in value]
            elif isinstance(value, str):
                suggestions[key] = [value]
            else:
                suggestions[key] = []
        
        if not isinstance(suggestions["summary"], str):
            suggestions["summary"] = str(suggestions["summary"])
        
        logger.info(
            "generate_chart_configs_and_suggestions_with_ai: suggestions sections - summary_present=%s, observations=%d, recommendations=%d",
            bool(suggestions.get("summary")),
            len(suggestions.get("key_observations", [])),
            len(suggestions.get("recommendations", [])),
        )

        return {
            "chart_configs": validated_configs,
            "suggestions": suggestions,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in generate_chart_configs_and_suggestions_with_ai: %s", str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error generating chart configurations and suggestions with AI: {str(e)}",
        )


def generate_report_suggestions_with_ai(report_data: List[Dict]) -> Dict[str, Any]:
    """
    Use OpenAI to generate business and data analysis suggestions for the report.
    
    Returns a structured JSON object with:
    - summary
    - key_observations
    - important_trends
    - detected_issues
    - business_insights
    - recommendations
    - suggested_charts
    """
    logger.info(
        "generate_report_suggestions_with_ai: rows=%d",
        len(report_data),
    )

    if not OPENAI_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="OpenAI library not available. Please install it with: pip install openai",
        )
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY environment variable is not set",
        )
    
    client = OpenAI(api_key=api_key)
    logger.info("OpenAI client created for suggestions-only call")
    
    # To control token usage, sample up to 50 rows but keep total count info
    sample_size = min(50, len(report_data))
    sample_data = report_data[:sample_size]
    
    # System prompt based directly on the user's requested analysis instructions
    system_prompt = """You are a business and data analyst.

Analyze the provided report data carefully and produce meaningful insights. 
Your goal is to identify trends, anomalies, risks, and opportunities in the data.

Steps to follow:

1. Understand the structure of the report and key fields such as revenue, costs, quantities, customer data, product data, dates, and other metrics.
2. Identify patterns and trends in the data (growth, decline, seasonality, unusual spikes).
3. Highlight important metrics such as totals, averages, ratios, and comparisons where relevant.
4. Detect any anomalies, inconsistencies, or possible data quality issues.
5. Provide business insights explaining what the data suggests about performance.
6. Suggest actionable recommendations based on the analysis.
7. Mention potential risks or areas that require attention.
8. If useful, propose additional metrics or visualizations that could help understand the data better.

Output format:

Return ONLY a valid JSON object with this exact structure:
{
  "summary": "Summary of the report",
  "key_observations": ["...", "..."],
  "important_trends": ["...", "..."],
  "detected_issues": ["...", "..."],
  "business_insights": ["...", "..."],
  "recommendations": ["...", "..."],
  "suggested_charts": ["...", "..."]
}

Keep the explanation clear, concise, and professional.
Avoid repeating raw data unless necessary for explaining insights.
Focus on interpretation rather than simple description."""

    # User prompt with context and (optionally truncated) data
    user_prompt = f"""You will receive tabular report data as JSON rows.

Total rows in report: {len(report_data)}.
Showing first {len(sample_data)} rows for analysis to stay within token limits:
{json.dumps(sample_data, indent=2)}

Analyze this data following the instructions from the system message and respond ONLY with a valid JSON object that matches the specified output format."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    try:
        start_time = time.time()
        response = call_openai_with_retry(client, messages)
        logger.info(
            "generate_report_suggestions_with_ai: OpenAI response received in %.2fs",
            time.time() - start_time,
        )
        
        if not isinstance(response, dict):
            raise ValueError("Suggestions response is not a JSON object")
        
        # Basic normalization: ensure all expected keys exist
        suggestions = {
            "summary": response.get("summary", ""),
            "key_observations": response.get("key_observations", []),
            "important_trends": response.get("important_trends", []),
            "detected_issues": response.get("detected_issues", []),
            "business_insights": response.get("business_insights", []),
            "recommendations": response.get("recommendations", []),
            "suggested_charts": response.get("suggested_charts", []),
        }
        
        # Ensure list fields are lists of strings
        for key in [
            "key_observations",
            "important_trends",
            "detected_issues",
            "business_insights",
            "recommendations",
            "suggested_charts",
        ]:
            value = suggestions.get(key, [])
            if isinstance(value, list):
                suggestions[key] = [str(item) for item in value]
            elif isinstance(value, str):
                suggestions[key] = [value]
            else:
                suggestions[key] = []
        
        # Summary should always be a string
        if not isinstance(suggestions["summary"], str):
            suggestions["summary"] = str(suggestions["summary"])
        
        logger.info(
            "generate_report_suggestions_with_ai: suggestions sections - summary_present=%s, observations=%d, recommendations=%d",
            bool(suggestions.get("summary")),
            len(suggestions.get("key_observations", [])),
            len(suggestions.get("recommendations", [])),
        )

        return suggestions
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in generate_report_suggestions_with_ai: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error generating report suggestions with AI: {str(e)}",
        )

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

@app.post("/api/analyze-ai")
async def analyze_report_with_ai(request: AIReportRequest):
    """
    Use AI to generate chart configurations and apply them to full report data
    
    This endpoint:
    1. Uses only first 10 rows for AI analysis (reduces token usage)
    2. Generates chart configurations using OpenAI
    3. Applies those configs to the FULL report data you sent
    4. Returns chart data ready to plot (points, labels, values, etc.)
    
    Best practices implemented:
    - Only uses first 10 rows for AI analysis (reduces token usage)
    - Applies configs to full dataset for accurate results
    - JSON mode for structured output
    - Retry logic with exponential backoff
    - Response validation
    - Error handling
    """
    try:
        if not request.report_data or len(request.report_data) == 0:
            raise HTTPException(status_code=400, detail="report_data is required and cannot be empty")
        
        # Store full report data
        full_report_data = request.report_data
        include_suggestions = request.include_suggestions
        report_prompt = request.report_prompt

        logger.info(
            "/api/analyze-ai: rows=%d, include_suggestions=%s, report_prompt=%r",
            len(full_report_data),
            include_suggestions,
            report_prompt,
        )

        # Use appropriate AI call based on whether suggestions are requested
        if include_suggestions:
            logger.info("/api/analyze-ai: calling combined charts+suggestions helper")
            # Single AI call to get BOTH chart configs and suggestions
            ai_result = generate_chart_configs_and_suggestions_with_ai(full_report_data, report_prompt=report_prompt)
            chart_configs = ai_result.get("chart_configs", [])
            suggestions = ai_result.get("suggestions", {})
        else:
            logger.info("/api/analyze-ai: calling charts-only helper (no suggestions)")
            # Only generate chart configurations, skip expensive suggestions
            chart_configs = generate_chart_configs_with_ai(full_report_data, report_prompt=report_prompt)
            # Return an empty suggestions structure with the expected shape
            suggestions = {
                "summary": "",
                "key_observations": [],
                "important_trends": [],
                "detected_issues": [],
                "business_insights": [],
                "recommendations": [],
                "suggested_charts": [],
            }
        
        # Convert to ChartConfig models for validation
        validated_configs = []
        for config_dict in chart_configs:
            try:
                config = ChartConfig(**config_dict)
                validated_configs.append(config)
            except Exception as e:
                # Skip invalid configs
                print(f"Warning: Invalid chart config skipped: {str(e)}")
                continue
        
        if len(validated_configs) == 0:
            raise HTTPException(
                status_code=500,
                detail="AI generated chart configurations, but none were valid"
            )
        
        logger.info(
            "/api/analyze-ai: %d validated chart configs, generating chart data",
            len(validated_configs),
        )

        # Apply chart configs to FULL report data and generate chart data
        charts = []
        for config in validated_configs:
            chart_data = analyze_data_for_chart(full_report_data, config)
            charts.append(chart_data)
        
        logger.info(
            "/api/analyze-ai: returning %d charts, suggestions_present=%s",
            len(charts),
            bool(suggestions.get("summary")) or bool(suggestions.get("key_observations")),
        )

        return JSONResponse(content={
            "success": True,
            "charts": charts,  # Chart data ready to plot
            "chart_configs": [config.model_dump() for config in validated_configs],  # For reference
            "report_count": len(full_report_data),
            "suggestions": suggestions  # New key with business/data analysis
        })
        
    except HTTPException:
        logger.exception("/api/analyze-ai: HTTPException")
        raise
    except Exception as e:
        logger.exception("/api/analyze-ai: unexpected error")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analyze-ai")
async def analyze_ai_info():
    """GET endpoint to show usage information for /api/analyze-ai"""
    return {
        "message": "AI Chart Configuration and Suggestions Endpoint",
        "method": "POST",
        "description": "Use POST method to send report data and get AI-generated chart configurations, chart data, and business analysis suggestions",
        "request_body": {
            "report_data": "Array of report data objects",
            "include_suggestions": "Optional boolean. If true (default), the AI also generates business/data suggestions. If false, only chart configurations are generated.",
            "report_prompt": "Optional string. A natural language description of what kind of report or insights the user wants (e.g., 'Focus on monthly sales trends and top products')."
        },
        "response": {
            "success": "boolean",
            "charts": "Array of chart data ready to plot",
            "chart_configs": "Array of AI-generated chart configurations",
            "report_count": "Number of rows in report",
            "suggestions": {
                "summary": "Summary of the report",
                "key_observations": "Array of key observations",
                "important_trends": "Array of important trends",
                "detected_issues": "Array of detected issues or anomalies",
                "business_insights": "Array of business insights",
                "recommendations": "Array of recommendations",
                "suggested_charts": "Array of suggested additional charts or visualizations"
            }
        },
        "example": {
            "method": "POST",
            "url": "/api/analyze-ai",
            "body": {
                "report_data": [
                    {"column1": "value1", "column2": 123}
                ],
                "include_suggestions": True,
                "report_prompt": "Focus on monthly sales trends and top-performing products"
            }
        }
    }

@app.get("/")
async def root():
    return {
        "message": "Report Analysis API",
        "endpoints": [
            "/api/analyze (POST/GET)",
            "/api/analyze-ai (POST only - use POST method)"
        ],
        "note": "Visit /api/analyze-ai with GET to see usage information"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

