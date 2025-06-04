"""
Test script for the enhanced election crawler.
This script tests basic functionality without performing a full crawl.
"""

import sys
import logging
from election_crawler import ElectionCrawler, ElectionCrawlerError


def test_basic_functionality():
    """Test basic crawler functionality."""
    print("Testing Enhanced Election Crawler")
    print("=" * 40)
    
    try:
        # Initialize crawler
        print("1. Initializing crawler...")
        crawler = ElectionCrawler()
        print("   ✓ Crawler initialized successfully")
        
        # Test fetching city and town codes
        print("2. Fetching city and town codes...")
        city_codes, town_codes = crawler.get_city_town_codes()
        print(f"   ✓ Found {len(city_codes)} cities")
        for i, city in enumerate(city_codes):
            print(f"   - {city.name} ({city.code})")
        print(f"   ✓ Found {len(town_codes)} initial town codes")
        
        # Test fetching town codes for first city
        if city_codes:
            first_city = city_codes[0]
            print(f"3. Fetching town codes for {first_city.name}...")
            town_codes_for_city = crawler.get_town_codes_for_city(first_city.code)
            print(f"   ✓ Found {len(town_codes_for_city)} town codes for {first_city.name}")
            
            # Display first few towns
            print("   Sample towns:")
            for i, town in enumerate(town_codes_for_city[:3]):
                print(f"   - {town.name} ({town.code})")
            if len(town_codes_for_city) > 3:
                print(f"   ... and {len(town_codes_for_city) - 3} more")
        
        print("\n" + "=" * 40)
        print("✓ All basic tests passed!")
        print("The crawler is ready for use.")
        print("\nTo start crawling:")
        print("  python election_crawler.py")
        print("\nFor help:")
        print("  python election_crawler.py --help")
        
        return True
        
    except ElectionCrawlerError as e:
        print(f"✗ Crawler error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_single_download():
    """Test downloading a single file (optional test)."""
    print("\nOptional: Test single file download")
    print("=" * 40)
    
    response = input("Do you want to test downloading one file? (y/N): ").strip().lower()
    if response != 'y':
        print("Skipping download test.")
        return True
    
    try:
        crawler = ElectionCrawler()
        city_codes, _ = crawler.get_city_town_codes()
        
        if not city_codes:
            print("✗ No cities found")
            return False
        
        # Use first city
        first_city = city_codes[0]
        town_codes = crawler.get_town_codes_for_city(first_city.code)
        
        if not town_codes:
            print(f"✗ No towns found for {first_city.name}")
            return False
        
        # Use first town
        first_town = town_codes[0]
        
        print(f"Testing download: {first_city.name} - {first_town.name}")
        success = crawler.download_excel_for_location(
            first_city.code, first_city.name,
            first_town.code, first_town.name
        )
        
        if success:
            print("✓ Single download test successful!")
            print(f"✓ File saved in: {crawler.download_dir}")
        else:
            print("✗ Download test failed")
        
        return success
        
    except Exception as e:
        print(f"✗ Download test error: {e}")
        return False


if __name__ == "__main__":
    # Set logging level for testing
    logging.getLogger().setLevel(logging.WARNING)
    
    print("Enhanced Election Crawler - Test Suite")
    print("=====================================")
    
    # Run basic functionality test
    basic_success = test_basic_functionality()
    
    if basic_success:
        # Optionally test single download
        test_single_download()
    else:
        print("\nBasic tests failed. Please check your configuration and internet connection.")
        sys.exit(1)
    
    print("\nTest completed!")
