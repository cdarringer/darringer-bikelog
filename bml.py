#!/usr/bin/env python3
"""Bike Maintenance Log"""

import argparse
import csv
import os
from datetime import datetime
from pathlib import Path

RIDES_DIR = "/Users/chris/git/darringer-bikelog/data/rides"
MAINTENANCE_DIR = "/Users/chris/git/darringer-bikelog/data/maintenance"
MAINTENANCE_CSV = os.path.join(MAINTENANCE_DIR, "maintenance.csv")

DEFAULT_BIKES = [
    "Cannondale M700",
    "Cannondale ST400",
    "Cannondale ST400 2",
    "Fuji",
    "Giant Boulder Jr.",
    "Jamis Laser 16",
    "Liv Alight",
    "Liv City",
    "Other",
    "Tommaso",
    "Tommaso 2",
    "Torelli",
    "Torelli 2"
]

CSV_COLUMNS = ['Date', 'Bike', 'Activity', 'Cost', 'Shop', 'Mileage_At_Service']


def get_bike_mileage(bike, as_of_date):
    """Sum all tracked miles for a bike up to and including as_of_date."""
    if isinstance(as_of_date, datetime):
        cutoff = as_of_date
    else:
        cutoff = datetime.strptime(as_of_date, '%Y-%m-%d')

    total = 0.0
    for path in sorted(Path(RIDES_DIR).glob('rides_[0-9]*.csv')):
        with open(path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('Bike', '').strip() != bike:
                    continue
                try:
                    row_date = datetime.strptime(row['Date'].strip(), '%m/%d/%Y')
                except ValueError:
                    continue
                if row_date <= cutoff:
                    try:
                        total += float(row['Distance'])
                    except ValueError:
                        pass
    return total


def ensure_csv_exists():
    os.makedirs(MAINTENANCE_DIR, exist_ok=True)
    if not os.path.exists(MAINTENANCE_CSV):
        with open(MAINTENANCE_CSV, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_COLUMNS)


def log_maintenance(date, bike, activity, cost, shop):
    """Prepend a new maintenance record (newest first)."""
    if isinstance(date, datetime):
        date_obj = date
    else:
        date_obj = datetime.strptime(date, '%Y-%m-%d')

    date_str = date_obj.strftime('%-m/%-d/%Y')
    mileage = get_bike_mileage(bike, date_obj)

    new_record = [date_str, bike, activity, f'{cost:.2f}', shop, f'{mileage:.1f}']

    existing = []
    if os.path.exists(MAINTENANCE_CSV):
        with open(MAINTENANCE_CSV, 'r', newline='') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if row:
                    existing.append(row)

    with open(MAINTENANCE_CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMNS)
        writer.writerow(new_record)
        for row in existing:
            writer.writerow(row)

    print(f"✓ Logged maintenance: {date_str} — {bike}")
    print(f"  Activity: {activity}")
    print(f"  Cost: ${cost:.2f}")
    if shop:
        print(f"  Shop: {shop}")
    print(f"  Mileage at service: {mileage:,.1f} miles")
    print(f"  Saved to {MAINTENANCE_CSV}")


def list_maintenance(bike=None, limit=20):
    if not os.path.exists(MAINTENANCE_CSV):
        print("No maintenance records found.")
        return

    with open(MAINTENANCE_CSV, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if any(r.values())]

    if bike:
        rows = [r for r in rows if r['Bike'] == bike]

    if not rows:
        print("No maintenance records found.")
        return

    shown = rows[:limit]
    header = f"{'Date':<12} {'Bike':<22} {'Activity':<42} {'Cost':>8} {'Miles':>8}"
    print(f"\n{header}")
    print("-" * len(header))
    for r in shown:
        try:
            cost_str = f"${float(r['Cost']):.2f}" if r['Cost'] else ''
        except ValueError:
            cost_str = ''
        try:
            miles_str = f"{float(r['Mileage_At_Service']):,.0f}" if r['Mileage_At_Service'] else ''
        except ValueError:
            miles_str = ''
        activity = r['Activity']
        if len(activity) > 41:
            activity = activity[:39] + '…'
        print(f"{r['Date']:<12} {r['Bike']:<22} {activity:<42} {cost_str:>8} {miles_str:>8}")

    if len(rows) > limit:
        print(f"\n  ({len(rows) - limit} more — use --limit to see more)")


def list_bikes():
    print("\nAvailable bikes:")
    for i, bike in enumerate(DEFAULT_BIKES, 1):
        print(f"  {i}. {bike}")


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date: {date_str}. Use YYYY-MM-DD")


def main():
    parser = argparse.ArgumentParser(
        description='Log bike maintenance',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python bml.py --bike "Cannondale ST400" --activity "Tune-up" --cost 75.00 --shop "Bicycles NYC"
  python bml.py --date 2026-04-15 --bike "Torelli" --activity "New chain" --cost 35.00
  python bml.py --list
  python bml.py --list --bike "Cannondale ST400" --limit 50
        """
    )
    parser.add_argument('--date', type=parse_date, default=datetime.now(),
                        help='Date of maintenance (YYYY-MM-DD, default: today)')
    parser.add_argument('--bike', type=str, help='Bike name')
    parser.add_argument('--activity', type=str, help='Description of maintenance performed')
    parser.add_argument('--cost', type=float, default=0.0, help='Cost in dollars (default: 0.00)')
    parser.add_argument('--shop', type=str, default='', help='Shop or vendor (optional)')
    parser.add_argument('--list', action='store_true', help='List recent maintenance records')
    parser.add_argument('--list-bikes', action='store_true', help='List available bikes')
    parser.add_argument('--limit', type=int, default=20,
                        help='Max records to show with --list (default: 20)')

    args = parser.parse_args()

    if args.list_bikes:
        list_bikes()
        return

    if args.list:
        list_maintenance(bike=args.bike, limit=args.limit)
        return

    if not args.bike:
        parser.error('--bike is required')
    if not args.activity:
        parser.error('--activity is required')

    if args.bike not in DEFAULT_BIKES:
        print(f"Warning: '{args.bike}' is not in the default bike list.")
        for bike in DEFAULT_BIKES:
            print(f"  - {bike}")
        response = input(f"\nDo you want to use '{args.bike}' anyway? (y/n): ")
        if response.lower() != 'y':
            print("Not logged.")
            return

    ensure_csv_exists()
    log_maintenance(args.date, args.bike, args.activity, args.cost, args.shop)


if __name__ == '__main__':
    main()
