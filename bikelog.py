#!/usr/bin/env python3
"""
Bike Ride Logging Utility

A command-line tool to log bike rides with date, name, distance, and bike selection.
Data is stored in CSV files organized by year (rides_YYYY.csv).
"""

import argparse
import configparser
import csv
import hashlib
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

CSV_DIR = "/Users/chris/git/darringer-bikelog/data/rides"
CONFIG_FILE = Path(__file__).parent / 'bikelog.ini'

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


def load_config():
    """Load configuration from bikelog.ini."""
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Config file not found: {CONFIG_FILE}\n"
            "Create bikelog.ini with:\n"
            "  [s3]\n"
            "  bucket = your-bucket-name\n"
            "  region = us-east-1\n"
            "  prefix = rides/"
        )
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    return config


def _md5_of_file(filepath):
    """Compute MD5 hash of a file."""
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def publish_to_s3():
    """Publish CSV files to S3, uploading only new or changed files."""
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        print("Error: boto3 is required for S3 publishing.")
        print("Install it with: pip install boto3")
        return

    config = load_config()
    bucket = config.get('s3', 'bucket')
    region = config.get('s3', 'region', fallback=None)
    prefix = config.get('s3', 'prefix', fallback='rides/')
    if prefix and not prefix.endswith('/'):
        prefix += '/'

    local_files = sorted(Path(CSV_DIR).glob('rides_*.csv'))
    if not local_files:
        print("No CSV files found to publish.")
        return

    s3 = boto3.client('s3', region_name=region)

    # Fetch existing S3 object ETags for the prefix
    s3_etags = {}
    try:
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get('Contents', []):
                s3_etags[obj['Key']] = obj['ETag'].strip('"')
    except ClientError as e:
        print(f"Error accessing S3 bucket '{bucket}': {e}")
        return

    uploaded = 0
    skipped = 0
    for local_path in local_files:
        s3_key = prefix + local_path.name
        local_md5 = _md5_of_file(local_path)
        if s3_key in s3_etags and s3_etags[s3_key] == local_md5:
            skipped += 1
        else:
            action = "Updating" if s3_key in s3_etags else "Uploading"
            print(f"  {action} {local_path.name}...")
            s3.upload_file(str(local_path), bucket, s3_key)
            uploaded += 1

    print(f"Publish complete: {uploaded} uploaded, {skipped} unchanged.")


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

    parser.add_argument(
        '--publish',
        action='store_true',
        help='Publish CSV files to S3 (only uploads new or changed files)'
    )

    args = parser.parse_args()

    # Handle publish option
    if args.publish:
        publish_to_s3()
        return

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
