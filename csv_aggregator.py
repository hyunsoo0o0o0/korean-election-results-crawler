#!/usr/bin/env python3
"""
CSV Aggregator for Korean Election Results

This script aggregates CSV election data from voting district level (투표구) 
to higher administrative levels: sido (시도), sigungu (시군구), and eupmyeondong (읍면동).
"""

import pandas as pd
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ElectionDataAggregator:
    """Aggregates Korean election data by administrative levels."""
    
    def __init__(self, input_file: str):
        """
        Initialize the aggregator with input CSV file.
        
        Args:
            input_file (str): Path to the input CSV file
        """
        self.input_file = Path(input_file)
        self.df = None
        self.numeric_columns = []
        self.admin_columns = ['시도명', '시군구명', '읍면동명']
        
    def load_data(self) -> pd.DataFrame:
        """Load and validate the CSV data."""
        try:
            logger.info(f"Loading data from {self.input_file}")
            self.df = pd.read_csv(self.input_file)
            logger.info(f"Loaded {len(self.df)} rows")
            
            # Validate required columns exist
            required_columns = ['시도명', '시군구명', '읍면동명']
            missing_columns = [col for col in required_columns if col not in self.df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Identify numeric columns to aggregate (exclude administrative columns and 투표구명)
            exclude_columns = ['시도명', '시군구명', '읍면동명', '투표구명']
            self.numeric_columns = [col for col in self.df.columns 
                                  if col not in exclude_columns and 
                                  pd.api.types.is_numeric_dtype(self.df[col]) or
                                  self._is_numeric_string_column(col)]
            
            logger.info(f"Identified numeric columns for aggregation: {self.numeric_columns}")
            
            # Convert numeric string columns to numeric
            for col in self.numeric_columns:
                if self.df[col].dtype == 'object':
                    # Handle comma-separated numbers (Korean number format)
                    self.df[col] = self.df[col].astype(str).str.replace(',', '').str.replace('', '0')
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
            
            return self.df
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def _is_numeric_string_column(self, column: str) -> bool:
        """Check if a column contains numeric data stored as strings."""
        if self.df[column].dtype != 'object':
            return False
        
        # Sample a few values to check if they're numeric
        sample_values = self.df[column].dropna().head(10)
        for value in sample_values:
            try:
                # Try to convert after removing commas
                float(str(value).replace(',', ''))
            except (ValueError, TypeError):
                return False
        return True
    
    def aggregate_by_sido(self) -> pd.DataFrame:
        """Aggregate data by sido (시도) level."""
        logger.info("Aggregating data by sido (시도)")
        
        grouped = self.df.groupby('시도명')[self.numeric_columns].sum().reset_index()
        grouped['집계수준'] = '시도'
        
        # Reorder columns
        column_order = ['시도명', '집계수준'] + self.numeric_columns
        return grouped[column_order]
    
    def aggregate_by_sigungu(self) -> pd.DataFrame:
        """Aggregate data by sigungu (시군구) level."""
        logger.info("Aggregating data by sigungu (시군구)")
        
        grouped = self.df.groupby(['시도명', '시군구명'])[self.numeric_columns].sum().reset_index()
        grouped['집계수준'] = '시군구'
        
        # Reorder columns
        column_order = ['시도명', '시군구명', '집계수준'] + self.numeric_columns
        return grouped[column_order]
    
    def aggregate_by_eupmyeondong(self) -> pd.DataFrame:
        """Aggregate data by eupmyeondong (읍면동) level."""
        logger.info("Aggregating data by eupmyeondong (읍면동)")
        
        grouped = self.df.groupby(['시도명', '시군구명', '읍면동명'])[self.numeric_columns].sum().reset_index()
        grouped['집계수준'] = '읍면동'
        
        # Reorder columns  
        column_order = ['시도명', '시군구명', '읍면동명', '집계수준'] + self.numeric_columns
        return grouped[column_order]
    
    def create_summary_statistics(self, aggregated_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Create summary statistics for each aggregation level."""
        logger.info("Creating summary statistics")
        
        summary_stats = []
        
        for level, data in aggregated_data.items():
            stats = {
                '집계수준': level,
                '총_행수': len(data),
                '총_선거인수': data['선거인수'].sum() if '선거인수' in data.columns else 0,
                '총_투표수': data['투표수'].sum() if '투표수' in data.columns else 0,
                '평균_투표율': (data['투표수'].sum() / data['선거인수'].sum() * 100) if '선거인수' in data.columns and data['선거인수'].sum() > 0 else 0
            }
            summary_stats.append(stats)
        
        return pd.DataFrame(summary_stats)
    
    def save_aggregated_data(self, output_dir: str = "aggregated_results") -> Dict[str, str]:
        """
        Save aggregated data to separate CSV files.
        
        Args:
            output_dir (str): Directory to save output files
            
        Returns:
            Dict[str, str]: Dictionary mapping aggregation level to output file path
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Perform aggregations
        aggregated_data = {
            'sido': self.aggregate_by_sido(),
            'sigungu': self.aggregate_by_sigungu(), 
            'eupmyeondong': self.aggregate_by_eupmyeondong()
        }
        
        # Save files
        output_files = {}
        for level, data in aggregated_data.items():
            filename = f"{level}_aggregated.csv"
            filepath = output_path / filename
            data.to_csv(filepath, index=False, encoding='utf-8-sig')
            output_files[level] = str(filepath)
            logger.info(f"Saved {level} aggregation to {filepath}")
        
        # Save summary statistics
        summary_stats = self.create_summary_statistics(aggregated_data)
        summary_path = output_path / "aggregation_summary.csv"
        summary_stats.to_csv(summary_path, index=False, encoding='utf-8-sig')
        output_files['summary'] = str(summary_path)
        logger.info(f"Saved summary statistics to {summary_path}")
        
        return output_files
    
    def generate_combined_report(self, output_dir: str = "aggregated_results") -> str:
        """
        Generate a combined report with all aggregation levels in one file.
        
        Args:
            output_dir (str): Directory to save output file
            
        Returns:
            str: Path to the combined report file
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Perform aggregations
        sido_data = self.aggregate_by_sido()
        sigungu_data = self.aggregate_by_sigungu()
        eupmyeondong_data = self.aggregate_by_eupmyeondong()
        
        # Combine all data with consistent columns
        all_columns = set()
        for df in [sido_data, sigungu_data, eupmyeondong_data]:
            all_columns.update(df.columns)
        
        # Standardize columns for each dataframe
        for df_name, df in [('sido', sido_data), ('sigungu', sigungu_data), ('eupmyeondong', eupmyeondong_data)]:
            for col in all_columns:
                if col not in df.columns:
                    if col in ['시도명', '시군구명', '읍면동명']:
                        df[col] = '' 
                    else:
                        df[col] = 0
        
        # Combine all dataframes
        combined_data = pd.concat([sido_data, sigungu_data, eupmyeondong_data], ignore_index=True)
        
        # Reorder columns logically
        admin_cols = ['시도명', '시군구명', '읍면동명', '집계수준']
        other_cols = [col for col in combined_data.columns if col not in admin_cols]
        column_order = admin_cols + sorted(other_cols)
        
        combined_data = combined_data[column_order]
        
        # Save combined report
        combined_path = output_path / "combined_aggregated_report.csv"
        combined_data.to_csv(combined_path, index=False, encoding='utf-8-sig')
        logger.info(f"Saved combined report to {combined_path}")
        
        return str(combined_path)


def main():
    """Main function to run the aggregation script."""
    parser = argparse.ArgumentParser(description="Aggregate Korean election CSV data by administrative levels")
    parser.add_argument("input_file", help="Input CSV file path")
    parser.add_argument("-o", "--output-dir", default="aggregated_results", 
                       help="Output directory for aggregated files (default: aggregated_results)")
    parser.add_argument("--combined", action="store_true", 
                       help="Generate combined report with all aggregation levels")
    parser.add_argument("--log-level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help="Logging level")
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        # Initialize aggregator
        aggregator = ElectionDataAggregator(args.input_file)
        
        # Load data
        aggregator.load_data()
        
        # Save aggregated data
        output_files = aggregator.save_aggregated_data(args.output_dir)
        
        # Generate combined report if requested
        if args.combined:
            combined_file = aggregator.generate_combined_report(args.output_dir)
            output_files['combined'] = combined_file
        
        # Print summary
        print("\n=== Aggregation Complete ===")
        for level, filepath in output_files.items():
            print(f"{level.capitalize()}: {filepath}")
        
        print(f"\nAll files saved to: {args.output_dir}")
        
    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
