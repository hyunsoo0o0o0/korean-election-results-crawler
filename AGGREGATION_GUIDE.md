# CSV Aggregation Guide

This guide explains how to aggregate Korean election CSV data by administrative levels using the `csv_aggregator.py` script.

## Overview

The CSV aggregator can transform detailed voting district data into aggregated summaries at three administrative levels:

1. **Sido (시도)** - City/Province level (e.g., 서울특별시, 부산광역시)
2. **Sigungu (시군구)** - District level (e.g., 종로구, 해운대구)  
3. **Eupmyeondong (읍면동)** - Town/Village level (e.g., 청운효자동, 소공동)

## Input Data Format

Your CSV file should contain these required columns:
- `시도명` (City/Province name)
- `시군구명` (District name)
- `읍면동명` (Town/Village name)
- `투표구명` (Voting district name) - optional, will be aggregated away
- Numeric columns (votes, counts, etc.) - will be summed up

Example input format:
```csv
시도명,시군구명,읍면동명,투표구명,선거인수,투표수,더불어민주당이재명,국민의힘김문수,개혁신당이준석,민주노동당권영국,무소속송진호,계,무효투표수,기권자수
서울특별시,종로구,거소·선상투표,,148,140,64,44,27,1,0,136,4,8
서울특별시,종로구,관외사전투표,,13110,13108,7527,3378,1810,260,12,12987,121,2
```

## Basic Usage

### Command Line Interface

```bash
# Basic aggregation - creates separate files for each level
python csv_aggregator.py your_data.csv

# Specify custom output directory
python csv_aggregator.py your_data.csv -o my_results

# Generate combined report with all levels in one file
python csv_aggregator.py your_data.csv --combined

# Enable debug logging
python csv_aggregator.py your_data.csv --log-level DEBUG
```

### Programmatic Usage

```python
from csv_aggregator import ElectionDataAggregator

# Initialize aggregator
aggregator = ElectionDataAggregator("your_data.csv")

# Load data
aggregator.load_data()

# Get aggregated data
sido_data = aggregator.aggregate_by_sido()
sigungu_data = aggregator.aggregate_by_sigungu()
eupmyeondong_data = aggregator.aggregate_by_eupmyeondong()

# Save all aggregations
output_files = aggregator.save_aggregated_data("output_directory")

# Generate combined report
combined_file = aggregator.generate_combined_report("output_directory")
```

## Output Files

The aggregator generates several output files:

### 1. Separate Aggregation Files
- `sido_aggregated.csv` - Province/City level aggregation
- `sigungu_aggregated.csv` - District level aggregation  
- `eupmyeondong_aggregated.csv` - Town/Village level aggregation
- `aggregation_summary.csv` - Summary statistics for each level

### 2. Combined Report (if --combined flag used)
- `combined_aggregated_report.csv` - All aggregation levels in one file

## Output Structure

### Sido Level Output
```csv
시도명,집계수준,선거인수,투표수,더불어민주당이재명,국민의힘김문수,...
서울특별시,시도,23521,21770,12675,5780,...
부산광역시,시도,6600,5300,2650,1850,...
```

### Sigungu Level Output  
```csv
시도명,시군구명,집계수준,선거인수,투표수,더불어민주당이재명,국민의힘김문수,...
서울특별시,종로구,시군구,20121,18570,11249,4945,...
서울특별시,중구,시군구,3400,3200,1700,1500,...
부산광역시,해운대구,시군구,4700,3800,1900,1300,...
```

### Eupmyeondong Level Output
```csv
시도명,시군구명,읍면동명,집계수준,선거인수,투표수,더불어민주당이재명,국민의힘김문수,...
서울특별시,종로구,거소·선상투표,읍면동,148,140,64,44,...
서울특별시,종로구,관외사전투표,읍면동,13110,13108,7527,3378,...
서울특별시,종로구,청운효자동,읍면동,8847,6822,2959,2789,...
```

## Features

### Automatic Data Type Handling
- Automatically detects numeric columns for aggregation
- Handles Korean number format with commas (e.g., "1,234" → 1234)
- Converts string numbers to proper numeric types
- Fills missing values with 0

### Flexible Column Support
- Works with any number of candidate columns
- Preserves all numeric data columns
- Adds aggregation level indicator column

### Summary Statistics
- Total rows per aggregation level
- Total voter counts and vote counts
- Average turnout rates
- Export to summary CSV file

## Example Workflow

1. **Prepare your data** - Ensure CSV has required columns (시도명, 시군구명, 읍면동명)

2. **Run basic aggregation**:
   ```bash
   python csv_aggregator.py reordered_merged_results.csv
   ```

3. **Check results** in the `aggregated_results` directory:
   - Review `aggregation_summary.csv` for overview
   - Use `sido_aggregated.csv` for province-level analysis
   - Use `sigungu_aggregated.csv` for district-level analysis
   - Use `eupmyeondong_aggregated.csv` for town-level analysis

4. **Optional: Generate combined report**:
   ```bash
   python csv_aggregator.py reordered_merged_results.csv --combined
   ```

## Troubleshooting

### Common Issues

**Missing Required Columns**
```
ValueError: Missing required columns: ['시도명']
```
- Ensure your CSV has the required administrative columns
- Check column names match exactly (including Korean characters)

**Encoding Issues**
- Files are saved with UTF-8-BOM encoding for Excel compatibility
- Use UTF-8 encoding when opening in text editors

**Memory Issues with Large Files**
- Process files in smaller chunks if needed
- Consider filtering data before aggregation

### Debug Mode
Enable debug logging to see detailed processing information:
```bash
python csv_aggregator.py your_data.csv --log-level DEBUG
```

## Integration with Existing Project

This aggregator works seamlessly with your existing Korean election crawler:

```bash
# Full pipeline
python election_crawler.py              # Download data
python html_to_csv_parser.py           # Convert to CSV  
python csv_merger.py                    # Merge files
python csv_column_reorder.py merged_election_results.csv  # Reorder columns
python csv_aggregator.py reordered_merged_results.csv --combined  # Aggregate
```

The aggregated data is perfect for analysis, visualization, and reporting at different administrative levels.
