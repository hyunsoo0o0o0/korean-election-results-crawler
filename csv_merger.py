"""
CSV Merger for Election Results

This script merges multiple CSV files from the csv_results directory into a single
consolidated file, adding city and town name columns and cleaning the data.
"""

import pandas as pd
import os
import re
from pathlib import Path
from typing import Dict, List
import logging
from election_crawler import ElectionCrawler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CSVMerger:
    """
    Merges election result CSV files with proper city/town name mapping.
    """
    
    def __init__(self, csv_dir: str = "csv_results", output_file: str = "merged_election_results.csv"):
        """
        Initialize the CSV merger.
        
        Args:
            csv_dir: Directory containing CSV files to merge
            output_file: Output filename for merged results
        """
        self.csv_dir = Path(csv_dir)
        self.output_file = output_file
        self.city_mapping = {}
        self.town_mapping = {}
        self.merged_data = []
        
    def fetch_location_mappings(self):
        """
        Fetch city and town code mappings using the existing ElectionCrawler.
        """
        logger.info("Fetching location mappings from election server...")
        
        try:
            crawler = ElectionCrawler()
            city_codes, _ = crawler.get_city_town_codes()
            
            # Build city mapping
            self.city_mapping = {city.code: city.name for city in city_codes}
            logger.info(f"Found {len(self.city_mapping)} city mappings")
            
            # Build town mapping by fetching towns for each city
            for city in city_codes:
                logger.info(f"Fetching towns for {city.name} ({city.code})")
                towns = crawler.get_town_codes_for_city(city.code)
                for town in towns:
                    self.town_mapping[town.code] = town.name
            
            logger.info(f"Found {len(self.town_mapping)} town mappings")
            
        except Exception as e:
            logger.error(f"Failed to fetch location mappings: {e}")
            raise
    
    def extract_codes_from_filename(self, filename: str):
        """
        Extract city and town codes from CSV filename.
        
        Args:
            filename: CSV filename in format election_report_{cityCode}_{townCode}_{timestamp}.csv
            
        Returns:
            Tuple of (city_code, town_code) or (None, None) if parsing fails
        """
        match = re.match(r'election_report_(\d+)_(\d+)_\d+\.csv', filename)
        if match:
            return match.group(1), match.group(2)
        return None, None
    
    def convert_comma_numbers(self, value):
        """
        Convert comma-separated number strings to integers.
        
        Args:
            value: String value that might contain comma-separated numbers
            
        Returns:
            Integer value or original value if conversion fails
        """
        if isinstance(value, str):
            # Remove quotes and commas, then try to convert to int
            cleaned = value.strip('"').replace(',', '')
            if cleaned.isdigit():
                return int(cleaned)
        return value
    
    def clean_dataframe(self, df: pd.DataFrame, city_name: str, town_name: str):
        """
        Clean and transform a single CSV dataframe.
        
        Args:
            df: Input dataframe
            city_name: City name to add
            town_name: Town name to add
            
        Returns:
            Cleaned dataframe
        """
        # Make a copy to avoid modifying original
        df = df.copy()
        
        # Add city and town name columns at the beginning
        df.insert(0, '시도명', city_name)
        df.insert(1, '시군구명', town_name)
        
        # Convert comma-separated numbers to integers for numeric columns
        numeric_columns = [
            '선거인수', '투표수', 
            '더불어민주당이재명', '국민의힘김문수', '개혁신당이준석', '민주노동당권영국', '무소속송진호', 
            '계', '무효투표수', '기권자수', 
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].apply(self.convert_comma_numbers)
        
        # Forward-fill empty 읍면동명 values
        if '읍면동명' in df.columns:
            # Replace empty strings with NaN for proper forward fill
            df['읍면동명'] = df['읍면동명'].replace('', pd.NA)
            df['읍면동명'] = df['읍면동명'].fillna(method='ffill')
        
        # Filter out only summary rows (not voting type rows)
        rows_to_remove = [
            '합계', '잘못 투입·구분된 투표지'
        ]
        
        if '읍면동명' in df.columns:
            df = df[~df['읍면동명'].isin(rows_to_remove)]


        # Filter out only summary rows (not voting type rows)
        rows_to_remove = [
            '소계'
        ]
        
        if '투표구명' in df.columns:
            df = df[~df['투표구명'].isin(rows_to_remove)]
        
        # # Remove rows where all voting numbers are 0
        # voting_cols = [col for col in numeric_columns if col in df.columns and col not in ['선거인수', '기권자수']]
        # if voting_cols:
        #     # Check if all voting columns are 0
        #     all_zeros = (df[voting_cols] == 0).all(axis=1)
        #     df = df[~all_zeros]
        
        return df
    
    def process_csv_files(self):
        """
        Process all CSV files in the directory and merge them.
        """
        if not self.csv_dir.exists():
            raise FileNotFoundError(f"CSV directory not found: {self.csv_dir}")
        
        csv_files = list(self.csv_dir.glob("*.csv"))
        logger.info(f"Found {len(csv_files)} CSV files to process")
        
        processed_count = 0
        
        for csv_file in csv_files:
            logger.info(f"Processing {csv_file.name}")
            
            # Extract codes from filename
            city_code, town_code = self.extract_codes_from_filename(csv_file.name)
            if not city_code or not town_code:
                logger.warning(f"Could not extract codes from filename: {csv_file.name}")
                continue
            
            # Get city and town names
            city_name = self.city_mapping.get(city_code, f"Unknown_City_{city_code}")
            town_name = self.town_mapping.get(town_code, f"Unknown_Town_{town_code}")
            
            if city_name.startswith("Unknown_"):
                logger.warning(f"Unknown city code: {city_code}")
            if town_name.startswith("Unknown_"):
                logger.warning(f"Unknown town code: {town_code}")
            
            try:
                # Read CSV file
                df = pd.read_csv(csv_file, encoding='utf-8')
                
                # Clean and transform
                cleaned_df = self.clean_dataframe(df, city_name, town_name)
                
                # Add to merged data
                self.merged_data.append(cleaned_df)
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing {csv_file.name}: {e}")
                continue
        
        logger.info(f"Successfully processed {processed_count} CSV files")
    
    def save_merged_results(self):
        """
        Save the merged results to a CSV file.
        """
        if not self.merged_data:
            logger.error("No data to save")
            return
        
        logger.info("Merging all dataframes...")
        merged_df = pd.concat(self.merged_data, ignore_index=True)
        
        logger.info(f"Merged dataframe shape: {merged_df.shape}")
        logger.info(f"Columns: {list(merged_df.columns)}")
        
        # Save to CSV
        logger.info(f"Saving to {self.output_file}")
        merged_df.to_csv(self.output_file, index=False, encoding='utf-8')
        
        # Print summary statistics
        self.print_summary_stats(merged_df)
    
    def print_summary_stats(self, df: pd.DataFrame):
        """
        Print summary statistics about the merged data.
        
        Args:
            df: Merged dataframe
        """
        logger.info("=" * 50)
        logger.info("MERGE SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total rows: {len(df):,}")
        logger.info(f"Total columns: {len(df.columns)}")
        
        if '시도명' in df.columns:
            cities = df['시도명'].nunique()
            logger.info(f"Unique cities: {cities}")
        
        if '시군구명' in df.columns:
            towns = df['시군구명'].nunique()
            logger.info(f"Unique towns: {towns}")
        
        if '읍면동명' in df.columns:
            districts = df['읍면동명'].nunique()
            logger.info(f"Unique districts: {districts}")
        
        # Show data types
        logger.info("\nColumn data types:")
        for col, dtype in df.dtypes.items():
            logger.info(f"  {col}: {dtype}")
        
        logger.info("=" * 50)
    
    def merge_all(self):
        """
        Execute the complete merge process.
        """
        logger.info("Starting CSV merge process...")
        
        try:
            # Step 1: Fetch location mappings
            self.fetch_location_mappings()
            
            # Step 2: Process CSV files
            self.process_csv_files()
            
            # Step 3: Save merged results
            self.save_merged_results()
            
            logger.info("CSV merge completed successfully!")
            
        except Exception as e:
            logger.error(f"Merge process failed: {e}")
            raise


def main():
    """Main entry point."""
    merger = CSVMerger()
    merger.merge_all()


if __name__ == "__main__":
    main()
