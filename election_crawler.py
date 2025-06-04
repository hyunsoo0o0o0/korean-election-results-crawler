"""
Enhanced Election Results Crawler for Korean National Election Commission

This module provides a robust crawler for downloading election results from
the Korean National Election Commission's website with improved error handling,
logging, and performance features.
"""

import requests
from bs4 import BeautifulSoup
import os
import time
import logging
import argparse
import json
from urllib.parse import unquote_plus
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from dataclasses import dataclass
import random

from config import *


@dataclass
class LocationInfo:
    """Data class for location information."""
    code: str
    name: str


class ElectionCrawlerError(Exception):
    """Custom exception for election crawler errors."""
    pass


class ElectionCrawler:
    """
    Enhanced election results crawler with improved error handling and features.
    """
    
    def __init__(self, election_id: str = DEFAULT_ELECTION_ID, 
                 election_code: str = DEFAULT_ELECTION_CODE,
                 download_dir: str = DOWNLOAD_DIR):
        """
        Initialize the election crawler.
        
        Args:
            election_id: The election ID to crawl
            election_code: The election type code
            download_dir: Directory to save downloaded files
        """
        self.election_id = election_id
        self.election_code = election_code
        self.download_dir = Path(download_dir)
        self.session = requests.Session()
        self.logger = self._setup_logging()
        self.stats = {
            'downloaded': 0,
            'errors': 0,
            'skipped': 0,
            'total_size': 0
        }
        
        # Setup session and create download directory
        self._setup_session()
        self._create_download_dir()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger(__name__)
        logger.setLevel(getattr(logging, LOG_LEVEL))
        
        # Avoid duplicate handlers
        if not logger.handlers:
            # File handler
            file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Formatter
            formatter = logging.Formatter(LOG_FORMAT)
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    def _setup_session(self):
        """Setup requests session with headers and configuration."""
        self.session.headers.update(HEADERS)
        self.session.headers['Referer'] = INIT_PAGE_URL
        
        # Configure request adapters for better reliability
        adapter = requests.adapters.HTTPAdapter(
            max_retries=requests.adapters.Retry(
                total=MAX_RETRIES,
                backoff_factor=0.3,
                status_forcelist=[500, 502, 503, 504]
            )
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def _create_download_dir(self):
        """Create download directory if it doesn't exist."""
        self.download_dir.mkdir(exist_ok=True)
        self.logger.info(f"Download directory: {self.download_dir.absolute()}")
    
    def _make_request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make HTTP request with retry logic and exponential backoff.
        
        Args:
            method: HTTP method (GET, POST)
            url: Target URL
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
            
        Raises:
            ElectionCrawlerError: If all retries fail
        """
        for attempt in range(MAX_RETRIES):
            try:
                # Add random jitter to avoid thundering herd
                if attempt > 0:
                    jitter = random.uniform(0.5, 1.5)
                    delay = RETRY_DELAY * (2 ** attempt) * jitter
                    self.logger.info(f"Retrying in {delay:.2f} seconds (attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(delay)
                
                kwargs.setdefault('timeout', TIMEOUT)
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt == MAX_RETRIES - 1:
                    raise ElectionCrawlerError(f"Failed to make request after {MAX_RETRIES} attempts: {e}")
        
        raise ElectionCrawlerError("Unexpected error in retry logic")
    
    def get_city_town_codes(self) -> Tuple[List[LocationInfo], List[LocationInfo]]:
        """
        Fetch city and town codes from the initial page.
        
        Returns:
            Tuple of (city_codes, all_town_codes)
        """
        self.logger.info("Fetching initial page to get city and town codes...")
        
        try:
            response = self._make_request_with_retry('GET', INIT_PAGE_URL)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract city codes
            city_select = soup.find('select', id='cityCode')
            city_codes = []
            if city_select:
                for option in city_select.find_all('option'):
                    value = option.get('value')
                    if value and value != '-1':
                        city_codes.append(LocationInfo(value, option.text.strip()))
            
            # Extract all town codes from the initial page
            town_select = soup.find('select', id='townCode')
            all_town_codes = []
            if town_select:
                for option in town_select.find_all('option'):
                    value = option.get('value')
                    if value and value != '-1':
                        all_town_codes.append(LocationInfo(value, option.text.strip()))
            
            self.logger.info(f"Found {len(city_codes)} cities and {len(all_town_codes)} initial town codes")
            return city_codes, all_town_codes
            
        except Exception as e:
            raise ElectionCrawlerError(f"Failed to fetch city/town codes: {e}")
    
    def get_town_codes_for_city(self, city_code: str) -> List[LocationInfo]:
        """
        Fetch town codes for a specific city via AJAX request.
        
        Args:
            city_code: The city code to fetch town codes for
            
        Returns:
            List of LocationInfo objects for towns in the city
        """
        params = {
            'electionId': self.election_id,
            'cityCode': city_code
        }
        
        try:
            response = self._make_request_with_retry('GET', TOWN_CODE_URL, params=params)
            response_data = response.json()
            
            # Handle nested JSON structure: jsonResult.body contains the town codes
            if 'jsonResult' in response_data and 'body' in response_data['jsonResult']:
                town_data = response_data['jsonResult']['body']
            else:
                # Fallback for direct array response
                town_data = response_data
            
            town_codes = []
            for item in town_data:
                if item.get('CODE') != '-1':
                    town_codes.append(LocationInfo(item['CODE'], item['NAME']))
            
            return town_codes
            
        except (requests.exceptions.RequestException, ValueError) as e:
            self.logger.error(f"Failed to fetch town codes for city {city_code}: {e}")
            return []
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe file system operations.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Ensure reasonable length
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:195] + ext
        
        return filename.strip()
    
    def _generate_title(self, city_name: str, town_name: str) -> str:
        """Generate title for the download request."""
        return f"[제21대 대통령선거] [{city_name}] [{town_name}]"
    
    def _file_exists_and_valid(self, filepath: Path) -> bool:
        """
        Check if file exists and is valid (not empty, reasonable size).
        Also checks for files with alternative extensions.
        
        Args:
            filepath: Path to the file
            
        Returns:
            True if file exists and appears valid
        """
        # Check the exact filepath first
        if filepath.exists():
            return self._validate_file_size(filepath)
        
        # Check for alternative extensions
        base_path = filepath.with_suffix('')
        alternative_extensions = ['.html', '.xls', '.xlsx']
        
        for ext in alternative_extensions:
            alt_filepath = base_path.with_suffix(ext)
            if alt_filepath.exists():
                self.logger.info(f"Found existing file with alternative extension: {alt_filepath}")
                return self._validate_file_size(alt_filepath)
        
        return False
    
    def _validate_file_size(self, filepath: Path) -> bool:
        """
        Validate that a file has reasonable size.
        
        Args:
            filepath: Path to the file
            
        Returns:
            True if file size is valid
        """
        size = filepath.stat().st_size
        if size < 512:  # Less than 512 bytes is probably not valid
            self.logger.warning(f"File {filepath} exists but is too small ({size} bytes)")
            return False
        
        return True
    
    def download_excel_for_location(self, city_code: str, city_name: str, 
                                  town_code: str, town_name: str) -> bool:
        """
        Download Excel file for a specific location.
        
        Args:
            city_code: City code
            city_name: City name
            town_code: Town code
            town_name: Town name
            
        Returns:
            True if download successful, False otherwise
        """
        statement_id = STATEMENT_ID_MAP.get(self.election_code, "VCCP08_#1")
        f_title = self._generate_title(city_name, town_name)
        
        payload = {
            "electionId": self.election_id,
            "requestURI": f"/electioninfo/{self.election_id}/vc/vccp08.jsp",
            "topMenuId": "VC",
            "secondMenuId": "VCCP08",
            "menuId": "VCCP08",
            "statementId": statement_id,
            "electionCode": self.election_code,
            "cityCode": city_code,
            "townCode": town_code,
            "reportType": "XLS",
            "fTitle": f_title,
        }
        
        self.logger.info(f"Downloading: {city_name} ({city_code}), {town_name} ({town_code})")
        
        try:
            response = self._make_request_with_retry('POST', REPORT_URL, data=payload, stream=True)
            
            # Determine filename
            filename = self._get_filename_from_response(response, city_code, town_code)
            filepath = self.download_dir / filename
            
            # Skip if file already exists and is valid
            if self._file_exists_and_valid(filepath):
                self.logger.info(f"File already exists and is valid: {filename}")
                self.stats['skipped'] += 1
                return True
            
            # Download file
            file_size = 0
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        file_size += len(chunk)
            
            # Validate downloaded content
            if self._validate_downloaded_content(filepath, filename):
                self.logger.info(f"Successfully downloaded: {filename} ({file_size:,} bytes)")
                self.stats['downloaded'] += 1
                self.stats['total_size'] += file_size
                return True
            else:
                self.logger.error(f"Downloaded file validation failed: {filename}")
                self.stats['errors'] += 1
                return False
            
        except Exception as e:
            self.logger.error(f"Error downloading for {city_name}, {town_name}: {e}")
            self.stats['errors'] += 1
            return False
    
    def _detect_content_type(self, response: requests.Response) -> str:
        """
        Detect the actual content type from response headers and content.
        
        Args:
            response: HTTP response object
            
        Returns:
            Detected content type ('html', 'excel', or 'unknown')
        """
        # Check Content-Type header first
        content_type = response.headers.get('Content-Type', '').lower()
        
        if 'text/html' in content_type or 'application/html' in content_type:
            return 'html'
        elif 'application/vnd.ms-excel' in content_type or 'application/excel' in content_type:
            return 'excel'
        elif 'application/octet-stream' in content_type:
            # Ambiguous content type, need to inspect content
            pass
        
        # Inspect the beginning of the content to determine type
        try:
            # Get first few kilobytes of content
            content_start = response.content[:4096].decode('utf-8', errors='ignore').lower()
            
            # Check for HTML indicators
            html_indicators = ['<!doctype html', '<html', '<head>', '<body>', '<table']
            if any(indicator in content_start for indicator in html_indicators):
                return 'html'
            
            # Check for Excel magic numbers or patterns
            # Excel files start with specific byte patterns
            content_bytes = response.content[:8]
            if (content_bytes.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1') or  # OLE2 header
                content_bytes.startswith(b'PK\x03\x04')):  # ZIP header (modern Excel)
                return 'excel'
                
        except (UnicodeDecodeError, AttributeError):
            # If we can't decode content, assume it's binary (Excel)
            return 'excel'
        
        return 'unknown'
    
    def _get_filename_from_response(self, response: requests.Response, 
                                  city_code: str, town_code: str) -> str:
        """
        Extract filename from response headers or generate one with proper extension.
        
        Args:
            response: HTTP response object
            city_code: City code for fallback filename
            town_code: Town code for fallback filename
            
        Returns:
            Sanitized filename with appropriate extension
        """
        # Detect actual content type
        content_type = self._detect_content_type(response)
        self.logger.debug(f"Detected content type: {content_type}")
        
        base_filename = None
        
        # Try to extract filename from headers
        if 'Content-Disposition' in response.headers:
            cd = response.headers['Content-Disposition']
            if 'filename=' in cd:
                try:
                    filename = cd.split('filename=')[1].strip('"\'')
                    # Decode URL-encoded filename
                    filename = unquote_plus(filename, encoding='utf-8')
                    filename = self._sanitize_filename(filename)
                    
                    # Remove existing extension to add correct one
                    base_filename = os.path.splitext(filename)[0]
                    
                except Exception as e:
                    self.logger.warning(f"Failed to parse filename from headers: {e}")
        
        # Generate base filename if not extracted from headers
        if not base_filename:
            timestamp = int(time.time())
            base_filename = f"election_report_{city_code}_{town_code}_{timestamp}"
        
        # Add appropriate extension based on content type
        if content_type == 'html':
            filename = f"{base_filename}.html"
            self.logger.info(f"Content detected as HTML, using extension: .html")
        elif content_type == 'excel':
            filename = f"{base_filename}.xls"
            self.logger.info(f"Content detected as Excel, using extension: .xls")
        else:
            # Default to .html since most responses seem to be HTML
            filename = f"{base_filename}.html"
            self.logger.warning(f"Unknown content type, defaulting to .html extension")
        
        self.logger.info(f"Final filename: {filename}")
        return filename
    
    def _validate_downloaded_content(self, filepath: Path, filename: str) -> bool:
        """
        Validate that the downloaded content is reasonable and matches expectations.
        
        Args:
            filepath: Path to the downloaded file
            filename: Name of the file for logging
            
        Returns:
            True if content is valid, False otherwise
        """
        try:
            # Check if file exists and has reasonable size
            if not filepath.exists():
                self.logger.error(f"Downloaded file does not exist: {filename}")
                return False
            
            size = filepath.stat().st_size
            if size < 512:
                self.logger.error(f"Downloaded file is too small ({size} bytes): {filename}")
                return False
            
            # Read first few KB to validate content
            with open(filepath, 'rb') as f:
                content_start = f.read(4096)
            
            # For HTML files, check for valid HTML structure
            if filename.lower().endswith('.html'):
                try:
                    content_text = content_start.decode('utf-8', errors='ignore').lower()
                    
                    # Check for basic HTML structure
                    has_html_tags = any(tag in content_text for tag in ['<html', '<table', '<tr', '<td'])
                    
                    if not has_html_tags:
                        self.logger.warning(f"HTML file doesn't contain expected HTML tags: {filename}")
                        # Don't fail completely, as some files might be valid but different format
                    
                    # Check for error indicators
                    error_indicators = ['error', 'exception', '404', '500', 'not found']
                    if any(indicator in content_text for indicator in error_indicators):
                        self.logger.warning(f"HTML file may contain error content: {filename}")
                        
                except UnicodeDecodeError:
                    self.logger.warning(f"Could not decode HTML file as UTF-8: {filename}")
            
            # For Excel files, check for valid Excel magic bytes
            elif filename.lower().endswith(('.xls', '.xlsx')):
                # Check for Excel file signatures
                is_ole2 = content_start.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1')  # OLE2
                is_zip = content_start.startswith(b'PK\x03\x04')  # ZIP (modern Excel)
                
                if not (is_ole2 or is_zip):
                    # Might be HTML content with .xls extension
                    try:
                        content_text = content_start.decode('utf-8', errors='ignore').lower()
                        if any(tag in content_text for tag in ['<html', '<table', '<tr']):
                            self.logger.info(f"File with .xls extension contains HTML content: {filename}")
                            # This is valid - server is returning HTML with .xls extension
                        else:
                            self.logger.warning(f"Excel file doesn't have expected file signature: {filename}")
                    except UnicodeDecodeError:
                        self.logger.warning(f"Could not validate Excel file content: {filename}")
            
            self.logger.debug(f"Content validation passed for: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating downloaded content for {filename}: {e}")
            return False
    
    def crawl_all_locations(self, use_concurrent: bool = False, max_workers: int = MAX_WORKERS):
        """
        Crawl election results for all locations.
        
        Args:
            use_concurrent: Whether to use concurrent downloads
            max_workers: Maximum number of concurrent workers
        """
        self.logger.info("Starting election results crawl...")
        start_time = time.time()
        
        try:
            city_codes, _ = self.get_city_town_codes()
            
            if use_concurrent:
                self._crawl_concurrent(city_codes, max_workers)
            else:
                self._crawl_sequential(city_codes)
            
            # Print final statistics
            elapsed_time = time.time() - start_time
            self._print_final_stats(elapsed_time)
            
        except KeyboardInterrupt:
            self.logger.info("Crawl interrupted by user")
        except Exception as e:
            self.logger.error(f"Crawl failed: {e}")
            raise
    
    def _crawl_sequential(self, city_codes: List[LocationInfo]):
        """Crawl locations sequentially."""
        for i, city in enumerate(city_codes, 1):
            self.logger.info(f"--- Processing city {i}/{len(city_codes)}: {city.name} ({city.code}) ---")
            
            town_codes = self.get_town_codes_for_city(city.code)
            if not town_codes:
                self.logger.warning(f"No town codes found for {city.name}. Skipping.")
                continue
            
            for town in town_codes:
                self.download_excel_for_location(city.code, city.name, town.code, town.name)
                time.sleep(BASE_DELAY + random.uniform(-0.2, 0.2))  # Add jitter
            
            # Longer pause between cities
            if i < len(city_codes):
                time.sleep(CITY_DELAY)
    
    def _crawl_concurrent(self, city_codes: List[LocationInfo], max_workers: int):
        """Crawl locations with concurrent downloads."""
        self.logger.info(f"Using concurrent downloads with {max_workers} workers")
        
        # Prepare all download tasks
        download_tasks = []
        for city in city_codes:
            town_codes = self.get_town_codes_for_city(city.code)
            for town in town_codes:
                download_tasks.append((city.code, city.name, town.code, town.name))
        
        self.logger.info(f"Total download tasks: {len(download_tasks)}")
        
        # Execute downloads concurrently
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(self.download_excel_for_location, *task): task 
                for task in download_tasks
            }
            
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    future.result()
                except Exception as e:
                    self.logger.error(f"Download task failed for {task}: {e}")
    
    def _print_final_stats(self, elapsed_time: float):
        """Print final crawling statistics."""
        total_files = self.stats['downloaded'] + self.stats['errors'] + self.stats['skipped']
        
        self.logger.info("=" * 50)
        self.logger.info("CRAWL COMPLETED")
        self.logger.info("=" * 50)
        self.logger.info(f"Total files processed: {total_files}")
        self.logger.info(f"Successfully downloaded: {self.stats['downloaded']}")
        self.logger.info(f"Skipped (already exists): {self.stats['skipped']}")
        self.logger.info(f"Errors: {self.stats['errors']}")
        self.logger.info(f"Total download size: {self.stats['total_size']:,} bytes")
        self.logger.info(f"Elapsed time: {elapsed_time:.2f} seconds")
        if self.stats['downloaded'] > 0:
            avg_time = elapsed_time / self.stats['downloaded']
            self.logger.info(f"Average time per download: {avg_time:.2f} seconds")
        self.logger.info("=" * 50)


def main():
    global LOG_LEVEL

    """Main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(description='Korean Election Results Crawler')
    parser.add_argument('--election-id', default=DEFAULT_ELECTION_ID, 
                       help='Election ID to crawl')
    parser.add_argument('--election-code', default=DEFAULT_ELECTION_CODE,
                       help='Election type code')
    parser.add_argument('--download-dir', default=DOWNLOAD_DIR,
                       help='Directory to save downloaded files')
    parser.add_argument('--concurrent', action='store_true',
                       help='Use concurrent downloads')
    parser.add_argument('--max-workers', type=int, default=MAX_WORKERS,
                       help='Maximum number of concurrent workers')
    parser.add_argument('--log-level', default=LOG_LEVEL,
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    
    args = parser.parse_args()
    
    # Update global config with command line arguments
    LOG_LEVEL = args.log_level
    
    # Create and run crawler
    crawler = ElectionCrawler(
        election_id=args.election_id,
        election_code=args.election_code,
        download_dir=args.download_dir
    )
    
    try:
        crawler.crawl_all_locations(
            use_concurrent=args.concurrent,
            max_workers=args.max_workers
        )
    except KeyboardInterrupt:
        print("\nCrawl interrupted by user")
    except Exception as e:
        print(f"Crawl failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
