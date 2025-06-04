# Korean Election Results Crawler

A comprehensive Python toolkit for downloading, parsing, and analyzing election results from the Korean National Election Commission (중앙선거관리위원회).

## Note by a human

This project is mostly LLM-generated, with the only exception of this section right here.
The project is released with no strings attached. (CC0, to be exact)
Cline + Claude Sonnet 4 is used for the vibe coding session.

## 🗳️ Overview

This project provides tools to systematically download election result files from the Korean National Election Commission's website, convert them to CSV format, and merge them into consolidated datasets for analysis. It supports various Korean election types including presidential, national assembly, and local elections.

## ✨ Features

### Core Crawler (`election_crawler.py`)
- **Robust Error Handling**: Automatic retry with exponential backoff
- **Rate Limiting**: Configurable delays with jitter to avoid overwhelming servers
- **Progress Tracking**: Comprehensive logging and statistics
- **File Validation**: Automatic deduplication and size checking
- **Concurrent Downloads**: Optional multi-threaded downloading
- **Korean Support**: Proper handling of Korean filenames and encoding
- **Command Line Interface**: Full CLI with configurable options

### Data Processing Pipeline
- **HTML to CSV Conversion**: Parse election result tables from HTML/XLS files
- **Data Merging**: Combine multiple CSV files with location mapping
- **Column Standardization**: Reorder columns to consistent format
- **Data Cleaning**: Handle comma-separated numbers and missing values

### Additional Tools
- **Test Suite**: Validate functionality before full crawls
- **Migration Guide**: Upgrade path from legacy implementations
- **Comprehensive Logging**: File and console logging with multiple levels

## 📦 Installation

### Prerequisites
- Python 3.7 or higher
- Internet connection for downloading election data

### Setup
1. Clone or download the project:
   ```bash
   git clone <repository-url>
   cd korean-election-results-crawler
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Test the installation:
   ```bash
   python test_crawler.py
   ```

## 🚀 Quick Start

### Basic Usage
Download all election results for the default election:
```bash
python election_crawler.py
```

### With Options
```bash
# Use concurrent downloads (faster)
python election_crawler.py --concurrent --max-workers 3

# Different election
python election_crawler.py --election-id 0020220309 --election-code 2

# Custom output directory
python election_crawler.py --download-dir my_election_data

# Enable debug logging
python election_crawler.py --log-level DEBUG
```

### Processing Pipeline
```bash
# 1. Download election results
python election_crawler.py

# 2. Convert HTML/XLS files to CSV
python html_to_csv_parser.py

# 3. Merge all CSV files
python csv_merger.py

# 4. Reorder columns (optional)
python csv_column_reorder.py merged_election_results.csv
```

## 📁 Project Structure

```
korean-election-results-crawler/
├── election_crawler.py      # Main crawler (enhanced)
├── config.py               # Configuration settings
├── html_to_csv_parser.py   # HTML/XLS to CSV converter
├── csv_merger.py           # CSV file merger
├── csv_column_reorder.py   # Column reordering utility
├── test_crawler.py         # Test suite
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── .gitignore             # Git ignore rules
└── reordered_merged_results.csv # Final processed data
```

## ⚙️ Configuration

### Election Settings (`config.py`)
- `DEFAULT_ELECTION_ID`: Election identifier (e.g., "0020250603")
- `DEFAULT_ELECTION_CODE`: Election type code (1=Presidential, 2=National Assembly, etc.)
- `DOWNLOAD_DIR`: Directory for downloaded files

### Performance Settings
- `MAX_WORKERS`: Concurrent download threads (default: 3)
- `BASE_DELAY`: Delay between requests (default: 1 second)
- `CITY_DELAY`: Delay between cities (default: 2 seconds)
- `MAX_RETRIES`: Maximum retry attempts (default: 3)

### Logging Configuration
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `LOG_FILE`: Log file location (default: 'election_crawler.log')

## 📊 Supported Election Types

| Code | Type | Korean Name |
|------|------|-------------|
| 1 | Presidential | 대통령선거 |
| 2 | National Assembly | 국회의원선거 |
| 3 | Local - Governor | 지방선거 - 시도지사 |
| 4 | Local - Mayor | 지방선거 - 시장군수구청장 |
| 5 | Metropolitan Council | 광역의회의원 |
| 6 | Basic Council | 기초의회의원 |
| 7 | Overseas Voting | 재외선거 |
| 8 | By-elections | 보궐선거 |

## 🔧 Advanced Usage

### Programmatic Usage
```python
from election_crawler import ElectionCrawler

# Create crawler instance
crawler = ElectionCrawler(
    election_id="0020250603",
    election_code="1",
    download_dir="my_results"
)

# Sequential crawling
crawler.crawl_all_locations()

# Concurrent crawling
crawler.crawl_all_locations(use_concurrent=True, max_workers=5)

# Access statistics
print(f"Downloaded: {crawler.stats['downloaded']}")
print(f"Errors: {crawler.stats['errors']}")
print(f"Total size: {crawler.stats['total_size']} bytes")
```

### Custom Data Processing
```python
from html_to_csv_parser import ElectionHTMLParser
from csv_merger import CSVMerger

# Parse HTML files to CSV
parser = ElectionHTMLParser("election_results", "csv_results")
stats = parser.parse_all_files()

# Merge CSV files
merger = CSVMerger("csv_results", "merged_results.csv")
merger.merge_all()
```

### Column Reordering
```python
from csv_column_reorder import reorder_csv_columns

# Reorder single file
reorder_csv_columns("merged_results.csv", "reordered_results.csv")

# Reorder multiple files
from csv_column_reorder import reorder_multiple_csv_files
reorder_multiple_csv_files("csv_results", "csv_results_reordered")
```

## 📋 Command Line Reference

### election_crawler.py
```bash
python election_crawler.py [OPTIONS]

Options:
  --election-id TEXT      Election ID to crawl (default: 0020250603)
  --election-code TEXT    Election type code (default: 1)
  --download-dir TEXT     Directory to save files (default: election_results)
  --concurrent           Use concurrent downloads
  --max-workers INTEGER  Maximum concurrent workers (default: 3)
  --log-level TEXT       Logging level (DEBUG, INFO, WARNING, ERROR)
  --help                 Show help message
```

### html_to_csv_parser.py
```bash
python html_to_csv_parser.py [OPTIONS]

Options:
  --input-dir TEXT       Directory containing HTML files (default: election_results)
  --output-dir TEXT      Directory to save CSV files (default: csv_results)
  --create-summary       Create summary CSV file
  --help                 Show help message
```

### csv_column_reorder.py
```bash
python csv_column_reorder.py [OPTIONS] INPUT

Arguments:
  INPUT                  Input CSV file or directory

Options:
  -o, --output TEXT      Output file or directory
  -d, --directory        Process all CSV files in directory
  -p, --pattern TEXT     File pattern for directory processing (default: *.csv)
  --help                 Show help message
```

## 🛠️ Data Schema

### Raw Election Data Columns
- `시도명`: City/Province name
- `시군구명`: District name  
- `읍면동명`: Town/Village name
- `투표구명`: Voting district name
- `선거인수`: Number of eligible voters
- `투표수`: Number of votes cast
- `[후보자명]`: Vote counts for each candidate
- `계`: Total valid votes
- `무효투표수`: Invalid votes
- `기권자수`: Abstentions

### Processed Data Features
- Consistent column ordering
- Numeric data type conversion
- Location name standardization
- Data validation and cleaning

## 🔍 Troubleshooting

### Common Issues

**Connection Errors**
```
ElectionCrawlerError: Failed to make request after 3 attempts
```
- Check internet connection
- Verify the election commission website is accessible
- Try reducing `MAX_WORKERS` for concurrent downloads

**Permission Errors**
```
PermissionError: [Errno 13] Permission denied
```
- Ensure write permissions to download directory
- Run with appropriate user privileges
- Check disk space availability

**Encoding Issues**
```
UnicodeDecodeError: 'utf-8' codec can't decode
```
- Files are automatically handled with proper Korean encoding
- Check if input files are corrupted
- Try re-downloading problematic files

**Memory Issues with Large Datasets**
- Process files in smaller batches
- Use the `--max-workers 1` option for sequential processing
- Increase system memory or use disk-based processing

### Debug Mode
Enable detailed logging:
```bash
python election_crawler.py --log-level DEBUG
```

Check log file:
```bash
tail -f election_crawler.log
```

### Testing
Validate functionality before full crawl:
```bash
python test_crawler.py
```

## 📝 Logging

The crawler provides comprehensive logging:

- **Console Output**: Progress and summary information
- **File Logging**: Detailed operation logs in `election_crawler.log`
- **Statistics**: Download counts, error rates, processing times

Log levels:
- `DEBUG`: Detailed debugging information
- `INFO`: General progress information (default)
- `WARNING`: Non-critical issues
- `ERROR`: Critical errors

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## ⚖️ Legal Notice

This tool is for educational and research purposes. Users are responsible for:
- Complying with the Korean National Election Commission's terms of service
- Respecting rate limits and server resources
- Using downloaded data in accordance with applicable laws

## 📄 License

This project is provided as-is for educational purposes. Please respect the terms of service of the Korean National Election Commission when using this tool.

## 🔗 Related Resources

- [Korean National Election Commission](http://info.nec.go.kr)
- [Election Data Portal](http://info.nec.go.kr/main/main_load.xhtml)
- [Python Requests Documentation](https://docs.python-requests.org/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
