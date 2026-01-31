#!/usr/bin/env python3
"""
Bike Ride Logging Utility

A command-line tool to log bike rides with date, name, distance, and bike selection.
Data is stored in CSV files organized by year (rides_YYYY.csv).
"""

import argparse
import csv
import os
from datetime import datetime
from pathlib import Path


# Default bike options - can be customized
DEFAULT_BIKES = [
    "Cannondale M700",
    "Cannondale ST400",
    "Cannondale ST400 2",
    "Fuji",
    "Giant Bouler Jr.",
    "Jamis Laser 16",
    "Liv Alight",
    "Liv City",
    "Other",
    "Tomamso",
    "Tomamso 2",
    "Torelli",
    "Torelli 2"
]

# Default rider options - can be customized
DEFAULT_RIDERS = [
    "Chris",
    "Frances",
    "Lucja",
    "Other",
    "Philip",
    "Sally",
    "Theo"
]

CSV_DIR = "/Users/chris/git/darringer-bikelog/rides"

def get_csv_filename(year=None):
    """Get the CSV filename for a given year."""
    if year is None:
        year = datetime.now().year
    return os.path.join(CSV_DIR, f"rides_{year}.csv")


def ensure_csv_exists(filename, year):
    """Create CSV file with headers if it doesn't exist."""
    os.makedirs(CSV_DIR, exist_ok=True)
    
    if not os.path.exists(filename):
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Name', 'Distance', 'Bike', 'Comment'])


def log_ride(date, name, distance, bike):
    """Log a bike ride to the appropriate CSV file."""
    # Parse the date to get the year
    if isinstance(date, str):
        date_obj = datetime.strptime(date, '%Y-%m-%d')
    else:
        date_obj = date
    
    year = date_obj.year
    filename = get_csv_filename(year)
    
    # Format date as MM/DD/YYYY
    date_str = date_obj.strftime('%-m/%-d/%Y')
    
    # Prepare the new record
    new_record = [date_str, name, distance, bike, '']
    
    # Read existing records if file exists
    existing_records = []
    file_exists = os.path.exists(filename)
    
    if file_exists:
        with open(filename, 'r', newline='') as f:
            reader = csv.reader(f)
            # Skip header row
            header = next(reader, None)
            # Read all existing data rows
            for row in reader:
                if row:  # Skip empty rows
                    existing_records.append(row)
    
    # Write header, new record, then existing records
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(['Date', 'Name', 'Distance', 'Bike', 'Comment'])
        # Write new record first (right after header)
        writer.writerow(new_record)
        # Write all existing records
        for row in existing_records:
            writer.writerow(row)
    
    print(f"✓ Logged ride: {date_str} - {name} rode {distance} miles on {bike}")
    print(f"  Saved to {filename}")


def list_bikes():
    """Display available bike options."""
    print("\nAvailable bikes:")
    for i, bike in enumerate(DEFAULT_BIKES, 1):
        print(f"  {i}. {bike}")


def list_riders():
    """Display available rider options."""
    print("\nAvailable riders:")
    for i, rider in enumerate(DEFAULT_RIDERS, 1):
        print(f"  {i}. {rider}")


def parse_date(date_str):
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


def main():
    parser = argparse.ArgumentParser(
        description='Log bike rides to CSV files organized by year',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Log a ride with defaults (today)
  python bikelog.py --rider "Chris" --bike "Cannondale ST400" --distance 15
  
  # Log a ride with custom date
  python bikelog.py --date 2024-01-15 --rider "Chris" --bike "Cannondale ST400" --distance 20
  
  # List available bikes
  python bikelog.py --list-bikes
  
  # List available riders
  python bikelog.py --list-riders
        """
    )
    
    parser.add_argument(
        '--date',
        type=parse_date,
        default=datetime.now(),
        help=f'Date of the ride (YYYY-MM-DD). Defaults to today ({datetime.now().strftime("%Y-%m-%d")})'
    )
    
    parser.add_argument(
        '--rider',
        type=str,
        help='Rider name. Use --list-riders to see available options (required unless using --list-bikes or --list-riders)'
    )
    
    parser.add_argument(
        '--bike',
        type=str,
        help='Bike used for the ride. Use --list-bikes to see available options (required unless using --list-bikes or --list-riders)'
    )
    
    parser.add_argument(
        '--distance',
        type=float,
        help='Distance of the ride in miles (required unless using --list-bikes or --list-riders)'
    )
    
    parser.add_argument(
        '--list-bikes',
        action='store_true',
        help='List available bike options and exit'
    )
    
    parser.add_argument(
        '--list-riders',
        action='store_true',
        help='List available rider options and exit'
    )
    
    args = parser.parse_args()
    
    # Handle list-bikes option
    if args.list_bikes:
        list_bikes()
        return
    
    # Handle list-riders option
    if args.list_riders:
        list_riders()
        return
    
    # Validate required arguments when not listing
    if args.distance is None:
        parser.error('--distance is required (use --list-bikes or --list-riders to see available options)')
    
    if args.rider is None:
        parser.error('--rider is required (use --list-riders to see available riders)')
    
    if args.bike is None:
        parser.error('--bike is required (use --list-bikes to see available bikes)')
    
    # Validate rider selection
    if args.rider not in DEFAULT_RIDERS:
        print(f"Warning: '{args.rider}' is not in the default rider list.")
        print("Available riders:")
        for rider in DEFAULT_RIDERS:
            print(f"  - {rider}")
        response = input(f"\nDo you want to use '{args.rider}' anyway? (y/n): ")
        if response.lower() != 'y':
            print("Ride not logged.")
            return
    
    # Validate bike selection
    if args.bike not in DEFAULT_BIKES:
        print(f"Warning: '{args.bike}' is not in the default bike list.")
        print("Available bikes:")
        for bike in DEFAULT_BIKES:
            print(f"  - {bike}")
        response = input(f"\nDo you want to use '{args.bike}' anyway? (y/n): ")
        if response.lower() != 'y':
            print("Ride not logged.")
            return
    
    # Log the ride
    log_ride(args.date, args.rider, args.distance, args.bike)


if __name__ == '__main__':
    main()
