#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV Column Reorder Script
Reorders CSV columns to match specified order for election data.
"""

import pandas as pd
import os
import glob
import argparse
from typing import List, Optional

def reorder_csv_columns(input_file: str, output_file: Optional[str] = None, 
                       desired_order: Optional[List[str]] = None) -> bool:
    """
    Reorder columns in a CSV file according to specified order.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file (if None, overwrites input)
        desired_order: List of column names in desired order
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    # Default column order as specified
    if desired_order is None:
        desired_order = [
            '시도명', '시군구명', '읍면동명', '투표구명', '선거인수', '투표수',
            '더불어민주당이재명', '국민의힘김문수', '개혁신당이준석', 
            '민주노동당권영국', '무소속송진호', '계', '무효투표수', '기권자수'
        ]
    
    try:
        # Read the CSV file
        df = pd.read_csv(input_file, encoding='utf-8')
        
        # Get current columns
        current_columns = list(df.columns)
        print(f"Current columns in {os.path.basename(input_file)}: {current_columns}")
        
        # Check if all desired columns exist in the dataframe
        missing_columns = [col for col in desired_order if col not in current_columns]
        if missing_columns:
            print(f"Warning: Missing columns in {input_file}: {missing_columns}")
        
        # Get available columns in desired order
        available_columns = [col for col in desired_order if col in current_columns]
        
        # Add any columns that exist in the file but not in desired order
        extra_columns = [col for col in current_columns if col not in desired_order]
        if extra_columns:
            print(f"Extra columns found (will be added at the end): {extra_columns}")
            available_columns.extend(extra_columns)
        
        # Reorder the dataframe
        df_reordered = df[available_columns]
        
        # Determine output file path
        if output_file is None:
            output_file = input_file
        
        # Save the reordered CSV
        df_reordered.to_csv(output_file, index=False, encoding='utf-8')
        print(f"Successfully reordered columns in {output_file}")
        print(f"New column order: {list(df_reordered.columns)}")
        
        return True
        
    except Exception as e:
        print(f"Error processing {input_file}: {str(e)}")
        return False

def reorder_multiple_csv_files(input_directory: str, output_directory: Optional[str] = None,
                              file_pattern: str = "*.csv") -> None:
    """
    Reorder columns in multiple CSV files.
    
    Args:
        input_directory: Directory containing CSV files
        output_directory: Directory to save reordered files (if None, overwrites originals)
        file_pattern: Pattern to match CSV files
    """
    
    # Get list of CSV files
    csv_files = glob.glob(os.path.join(input_directory, file_pattern))
    
    if not csv_files:
        print(f"No CSV files found in {input_directory} matching pattern {file_pattern}")
        return
    
    print(f"Found {len(csv_files)} CSV files to process")
    
    # Create output directory if specified
    if output_directory and not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    successful_count = 0
    failed_count = 0
    
    for csv_file in csv_files:
        print(f"\nProcessing: {csv_file}")
        
        # Determine output file path
        if output_directory:
            output_file = os.path.join(output_directory, os.path.basename(csv_file))
        else:
            output_file = None
        
        # Process the file
        if reorder_csv_columns(csv_file, output_file):
            successful_count += 1
        else:
            failed_count += 1
    
    print(f"\n=== Summary ===")
    print(f"Successfully processed: {successful_count} files")
    print(f"Failed to process: {failed_count} files")

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description="Reorder CSV columns for election data")
    parser.add_argument("input", help="Input CSV file or directory")
    parser.add_argument("-o", "--output", help="Output file or directory")
    parser.add_argument("-d", "--directory", action="store_true", 
                       help="Process all CSV files in directory")
    parser.add_argument("-p", "--pattern", default="*.csv", 
                       help="File pattern for directory processing (default: *.csv)")
    
    args = parser.parse_args()
    
    if args.directory:
        # Process multiple files in directory
        reorder_multiple_csv_files(args.input, args.output, args.pattern)
    else:
        # Process single file
        reorder_csv_columns(args.input, args.output)

if __name__ == "__main__":
    # If run directly, you can uncomment one of these examples:
    
    # Example 1: Process a single file
    # reorder_csv_columns("merged_election_results.csv", "reordered_election_results.csv")
    
    # Example 2: Process all CSV files in csv_results directory
    # reorder_multiple_csv_files("csv_results", "csv_results_reordered")
    
    # Example 3: Process all CSV files in csv_results directory (overwrite originals)
    # reorder_multiple_csv_files("csv_results")
    
    # Run the command line interface
    main()
