"""Configuration settings for the election crawler."""

import os

# Election settings
DEFAULT_ELECTION_ID = "0020250603"
DEFAULT_ELECTION_CODE = "1"  # Presidential election

# URLs
BASE_URL = "http://info.nec.go.kr"
REPORT_URL = f"{BASE_URL}/electioninfo/electionInfo_report.xhtml"
INIT_PAGE_URL = f"{BASE_URL}/main/showDocument.xhtml?electionId={DEFAULT_ELECTION_ID}&topMenuId=VC&secondMenuId=VCCP08"
TOWN_CODE_URL = f"{BASE_URL}/bizcommon/selectbox/selectbox_townCodeJson.json"

# Download settings
DOWNLOAD_DIR = "election_results"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
BASE_DELAY = 1  # seconds between requests
CITY_DELAY = 2  # seconds between cities
CHUNK_SIZE = 8192

# Request settings
TIMEOUT = 30  # seconds
MAX_WORKERS = 3  # for concurrent downloads

# Headers for better browser simulation
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/excel, application/vnd.ms-excel, application/x-msexcel, application/csv, text/csv, application/octet-stream, */*",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'
LOG_FILE = 'election_crawler.log'

# Statement ID mappings for different election types
STATEMENT_ID_MAP = {
    "1": "VCCP08_#1",      # Presidential
    "2": "VCCP08_#2_1",    # National Assembly
    "3": "VCCP08_#3",      # Local elections - Governor
    "4": "VCCP08_#4",      # Local elections - Mayor
    "5": "VCCP08_#5",      # Metropolitan council
    "6": "VCCP08_#6",      # Basic council
    "7": "VCCP08_#7_1",    # Overseas voting
    "8": "VCCP08_#8",      # By-elections
    "9": "VCCP08_#9",      # Referendum
    "10": "VCCP08_#10",    # Others
    "11": "VCCP08_#11"     # Constitutional referendum
}
