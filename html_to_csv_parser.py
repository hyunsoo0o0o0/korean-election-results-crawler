"""
HTML Election Results Parser - Convert HTML tables to CSV

This script parses the HTML election results files downloaded by the crawler
and converts them to clean CSV format for easier data analysis.
"""

import os
import pandas as pd
from bs4 import BeautifulSoup
import csv
from pathlib import Path
import argparse
from typing import List, Dict, Any
import re


class ElectionHTMLParser:
    """Parser for Korean election results HTML files."""
    
    def __init__(self, input_dir: str = "election_results", output_dir: str = "csv_results"):
        """
        Initialize the parser.
        
        Args:
            input_dir: Directory containing HTML files
            output_dir: Directory to save CSV files
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def parse_html_file(self, html_file: Path) -> List[Dict[str, Any]]:
        """
        Parse a single HTML file and extract table data.
        
        Args:
            html_file: Path to HTML file
            
        Returns:
            List of dictionaries containing row data
        """
        print(f"Parsing: {html_file.name}")
        
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find the main data table
        table = soup.find('table', {'id': 'table01'}) or soup.find('table', class_='table01')
        
        if not table:
            print(f"Warning: No data table found in {html_file.name}")
            return []
        
        # Extract headers
        headers = self._extract_headers(table)
        print(f"Found {len(headers)} columns: {headers[:5]}...")  # Show first 5 headers
        
        # Extract data rows
        data_rows = self._extract_data_rows(table, headers)
        print(f"Extracted {len(data_rows)} data rows")
        
        return data_rows
    
    def _extract_headers(self, table) -> List[str]:
        """Extract and clean table headers."""
        headers = []
        
        # Find header rows (usually in thead)
        thead = table.find('thead')
        if thead:
            header_rows = thead.find_all('tr')
        else:
            # Fallback: look for first few rows with th elements
            header_rows = table.find_all('tr')[:2]
        
        # Process header rows to handle rowspan/colspan
        if len(header_rows) >= 2:
            # Two-row header structure
            first_row = header_rows[0].find_all(['th', 'td'])
            second_row = header_rows[1].find_all(['th', 'td'])
            
            headers = []
            for cell in first_row:
                text = self._clean_text(cell.get_text())
                colspan = int(cell.get('colspan', 1))
                rowspan = int(cell.get('rowspan', 1))
                
                if rowspan == 2:
                    # Cell spans both rows
                    headers.append(text)
                else:
                    # Cell only in first row, get subcells from second row
                    if text == "후보자별 득표수":
                        # Special handling for candidate columns
                        candidate_cells = second_row[:colspan]
                        for candidate_cell in candidate_cells:
                            candidate_text = self._clean_text(candidate_cell.get_text())
                            headers.append(candidate_text)
                        # Remove processed cells from second_row
                        second_row = second_row[colspan:]
                    else:
                        headers.append(text)
            
            # Add remaining cells from second row
            for cell in second_row:
                text = self._clean_text(cell.get_text())
                headers.append(text)
        else:
            # Single row header
            header_cells = header_rows[0].find_all(['th', 'td'])
            headers = [self._clean_text(cell.get_text()) for cell in header_cells]
        
        return headers
    
    def _extract_data_rows(self, table, headers: List[str]) -> List[Dict[str, Any]]:
        """Extract data rows from table."""
        tbody = table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
        else:
            # Skip header rows
            all_rows = table.find_all('tr')
            rows = all_rows[2:] if len(all_rows) > 2 else all_rows[1:]
        
        data_rows = []
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) == 0:
                continue
            
            row_data = {}
            
            # Map cells to headers
            for i, cell in enumerate(cells):
                if i < len(headers):
                    cell_text = self._clean_text(cell.get_text())
                    row_data[headers[i]] = cell_text
                else:
                    # Extra cells (shouldn't happen with proper headers)
                    row_data[f'Extra_Column_{i}'] = self._clean_text(cell.get_text())
            
            # Fill missing columns with empty values
            for header in headers:
                if header not in row_data:
                    row_data[header] = ''
            
            data_rows.append(row_data)
        
        return data_rows
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ''
        
        # Remove extra whitespace and line breaks
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common HTML artifacts
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        return text
    
    def save_to_csv(self, data_rows: List[Dict[str, Any]], output_file: Path):
        """Save data to CSV file."""
        if not data_rows:
            print(f"No data to save for {output_file}")
            return
        
        # Get all unique headers from all rows
        all_headers = set()
        for row in data_rows:
            all_headers.update(row.keys())
        
        # Sort headers for consistent column order
        headers = sorted(list(all_headers))
        
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data_rows)
        
        print(f"Saved CSV: {output_file} ({len(data_rows)} rows, {len(headers)} columns)")
    
    def parse_all_files(self) -> Dict[str, int]:
        """
        Parse all HTML files in input directory.
        
        Returns:
            Dictionary with processing statistics
        """
        html_files = list(self.input_dir.glob("*.xls")) + list(self.input_dir.glob("*.html"))
        
        if not html_files:
            print(f"No HTML files found in {self.input_dir}")
            return {'processed': 0, 'errors': 0}
        
        stats = {'processed': 0, 'errors': 0, 'total_rows': 0}
        
        for html_file in html_files:
            try:
                # Parse HTML file
                data_rows = self.parse_html_file(html_file)
                
                if data_rows:
                    # Generate output filename
                    csv_filename = html_file.stem + '.csv'
                    output_file = self.output_dir / csv_filename
                    
                    # Save to CSV
                    self.save_to_csv(data_rows, output_file)
                    
                    stats['processed'] += 1
                    stats['total_rows'] += len(data_rows)
                else:
                    print(f"No data extracted from {html_file.name}")
                    stats['errors'] += 1
                    
            except Exception as e:
                print(f"Error processing {html_file.name}: {e}")
                stats['errors'] += 1
        
        return stats
    
    def create_summary_csv(self):
        """Create a summary CSV combining key data from all files."""
        csv_files = list(self.output_dir.glob("*.csv"))
        
        if not csv_files:
            print("No CSV files found to create summary")
            return
        
        summary_data = []
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                
                # Extract location info from filename or first rows
                location_info = self._extract_location_info(csv_file, df)
                
                # Get summary statistics
                if not df.empty and '합계' in df.iloc[:, 0].values:
                    # Find the summary row (합계)
                    summary_row = df[df.iloc[:, 0] == '합계'].iloc[0]
                    
                    summary_data.append({
                        'File': csv_file.name,
                        'City': location_info.get('city', ''),
                        'District': location_info.get('district', ''),
                        'Total_Eligible_Voters': self._safe_int(summary_row.get('선거인수', 0)),
                        'Total_Votes_Cast': self._safe_int(summary_row.get('투표수', 0)),
                        'Invalid_Votes': self._safe_int(summary_row.get('무효 투표수', 0)),
                        'Abstentions': self._safe_int(summary_row.get('기권자수', 0)),
                        'Voter_Turnout_Pct': self._calculate_turnout(
                            summary_row.get('선거인수', 0), 
                            summary_row.get('투표수', 0)
                        )
                    })
                    
            except Exception as e:
                print(f"Error processing {csv_file.name} for summary: {e}")
        
        if summary_data:
            summary_file = self.output_dir / "election_summary.csv"
            pd.DataFrame(summary_data).to_csv(summary_file, index=False, encoding='utf-8-sig')
            print(f"Created summary file: {summary_file}")
    
    def _extract_location_info(self, csv_file: Path, df: pd.DataFrame) -> Dict[str, str]:
        """Extract location information from filename or data."""
        # Try to extract from filename pattern
        filename = csv_file.stem
        
        # Pattern: election_report_CITYCODE_DISTRICTCODE_TIMESTAMP
        parts = filename.split('_')
        if len(parts) >= 4:
            city_code = parts[2]
            district_code = parts[3]
            
            # Map codes to names (you can expand this)
            city_map = {
                '1100': '서울특별시',
                '2600': '부산광역시',
                '2700': '대구광역시'
            }
            
            return {
                'city': city_map.get(city_code, city_code),
                'district': district_code  # Could map district codes too
            }
        
        return {'city': '', 'district': ''}
    
    def _safe_int(self, value) -> int:
        """Safely convert value to integer."""
        if pd.isna(value):
            return 0
        
        try:
            # Remove commas and convert
            if isinstance(value, str):
                value = value.replace(',', '').replace(' ', '')
            return int(float(value))
        except (ValueError, TypeError):
            return 0
    
    def _calculate_turnout(self, eligible, votes_cast) -> float:
        """Calculate voter turnout percentage."""
        eligible_int = self._safe_int(eligible)
        votes_int = self._safe_int(votes_cast)
        
        if eligible_int > 0:
            return round((votes_int / eligible_int) * 100, 2)
        return 0.0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Convert HTML election results to CSV')
    parser.add_argument('--input-dir', default='election_results',
                       help='Directory containing HTML files')
    parser.add_argument('--output-dir', default='csv_results',
                       help='Directory to save CSV files')
    parser.add_argument('--create-summary', action='store_true',
                       help='Create summary CSV file')
    
    args = parser.parse_args()
    
    # Create parser instance
    html_parser = ElectionHTMLParser(args.input_dir, args.output_dir)
    
    print("HTML to CSV Election Results Parser")
    print("=" * 40)
    print(f"Input directory: {args.input_dir}")
    print(f"Output directory: {args.output_dir}")
    print()
    
    # Parse all files
    stats = html_parser.parse_all_files()
    
    # Create summary if requested
    if args.create_summary:
        print("\nCreating summary CSV...")
        html_parser.create_summary_csv()
    
    # Print final statistics
    print("\n" + "=" * 40)
    print("PARSING COMPLETED")
    print("=" * 40)
    print(f"Files processed: {stats['processed']}")
    print(f"Errors: {stats['errors']}")
    print(f"Total data rows: {stats.get('total_rows', 0)}")
    print(f"Output directory: {args.output_dir}")
    print("=" * 40)


if __name__ == "__main__":
    main()
