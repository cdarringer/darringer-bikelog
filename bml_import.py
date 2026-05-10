#!/usr/bin/env python3
"""One-time import of legacy maintenance records from spreadsheets into maintenance.csv."""

import csv
import os
from datetime import datetime

from bml import MAINTENANCE_DIR, MAINTENANCE_CSV, CSV_COLUMNS

# All records parsed from the 7 source spreadsheets.
LEGACY_RECORDS = [
    # --- Giant Boulder Jr. ---
    {'date': '2023-10-15', 'bike': 'Giant Boulder Jr.', 'activity': 'New rear tube',
     'cost': 9.80, 'shop': 'Bicycles NYC'},

    # --- Tommaso 2 ---
    {'date': '2025-09-11', 'bike': 'Tommaso 2', 'activity': 'New Chain',
     'cost': 46.00, 'shop': 'Penn State Bikes'},
    {'date': '2025-06-28', 'bike': 'Tommaso 2', 'activity': 'Replaced front derailleur cable',
     'cost': 25.00, 'shop': 'Bikeway Mahopac'},
    {'date': '2025-06-27', 'bike': 'Tommaso 2', 'activity': 'Rotate Kenda tires',
     'cost': 0.00, 'shop': ''},
    {'date': '2024-11-24', 'bike': 'Tommaso 2',
     'activity': 'Cateye Urban wireless computer — previous Strata computer was defective',
     'cost': 44.95, 'shop': 'Amazon'},
    {'date': '2024-04-12', 'bike': 'Tommaso 2', 'activity': 'Replaced rear derailleur cable',
     'cost': 9.00, 'shop': 'Bicycles NYC'},
    {'date': '2023-05-27', 'bike': 'Tommaso 2', 'activity': 'Assembly and pedals with cages',
     'cost': 106.98, 'shop': 'Pedals & Petals'},
    {'date': '2023-04-11', 'bike': 'Tommaso 2',
     'activity': 'Original purchase with 2 bottle cages; shipped to Pedals & Petals for assembly',
     'cost': 1174.97, 'shop': 'Tomasso'},

    # --- Liv City ---
    {'date': '2022-12-31', 'bike': 'Liv City', 'activity': 'New rear brake pads',
     'cost': 13.85, 'shop': 'Amazon.com'},
    {'date': '2022-12-31', 'bike': 'Liv City', 'activity': 'Rotated tires front to back',
     'cost': 0.00, 'shop': ''},

    # --- Torelli ---
    {'date': '2025-12-14', 'bike': 'Torelli', 'activity': 'New Pacenti Brevet wheels',
     'cost': 265.00, 'shop': 'Pacenti Cycle Design'},
    {'date': '2025-05-26', 'bike': 'Torelli',
     'activity': 'New Pacenti wheel build; rear campy hub overhauled — Spoke Sapim Leader SL 2.0 298/300',
     'cost': 344.05, 'shop': 'Bicycles NYC'},
    {'date': '2024-10-12', 'bike': 'Torelli',
     'activity': 'Replace spoke on rear wheel non-drive side (Eastons)',
     'cost': 34.84, 'shop': 'Bicycles NYC'},
    {'date': '2023-10-28', 'bike': 'Torelli',
     'activity': 'New Campagnolo cables and cable housings; new brake pads; replaced barrel adjusters; new handlebar tape',
     'cost': 238.40, 'shop': 'Bicycles NYC'},
    {'date': '2023-10-12', 'bike': 'Torelli', 'activity': 'Swapped front and back tires',
     'cost': 0.00, 'shop': ''},
    {'date': '2022-08-02', 'bike': 'Torelli', 'activity': 'New Torelli Bormio seat (free from Todd)',
     'cost': 0.00, 'shop': 'Torelli'},
    {'date': '2022-06-06', 'bike': 'Torelli', 'activity': 'New front derailleur cable',
     'cost': 45.73, 'shop': 'Bicycles NYC'},
    {'date': '2022-01-08', 'bike': 'Torelli',
     'activity': 'Headset overhaul — bottom bracket and wheels all have cartridge bearings',
     'cost': 59.88, 'shop': "Conrad's Bike Shop"},
    {'date': '2021-10-09', 'bike': 'Torelli',
     'activity': 'Cinelli Vai Folli seatpost 27.2mm — original Athena seatpost cracked',
     'cost': 79.99, 'shop': 'Amazon.com'},
    {'date': '2021-09-15', 'bike': 'Torelli',
     'activity': 'Wahoo Speedplay Zero stainless steel pedals and cleats',
     'cost': 230.00, 'shop': 'REI'},
    {'date': '2021-09-26', 'bike': 'Torelli', 'activity': 'Vittoria Rubino Pro Road Tire 700x25c',
     'cost': 79.98, 'shop': 'Performance Bike'},
    {'date': '2021-08-28', 'bike': 'Torelli', 'activity': 'Campagnolo Record 9 Speed chain',
     'cost': 40.99, 'shop': 'Performance Bike'},
    {'date': '2021-06-01', 'bike': 'Torelli', 'activity': 'New Torelli Bormio XC seat',
     'cost': 85.00, 'shop': 'Torelli'},
    {'date': '2012-08-13', 'bike': 'Torelli',
     'activity': 'Sidi G5 Pro shoes and Speedplay cleat covers',
     'cost': 309.97, 'shop': 'Performance Bike'},
    {'date': '2010-10-03', 'bike': 'Torelli',
     'activity': 'Continental Gatorskin Tires 700x25c — lasted over 7k miles!',
     'cost': 80.97, 'shop': 'Bike Nasbar'},
    {'date': '2010-10-03', 'bike': 'Torelli', 'activity': 'New Easton EA50 wheels',
     'cost': 299.00, 'shop': 'Bike Nasbar'},

    # --- Cannondale ST400 ---
    {'date': '2025-06-07', 'bike': 'Cannondale ST400', 'activity': 'Put original wheels back on',
     'cost': 0.00, 'shop': ''},
    {'date': '2025-05-26', 'bike': 'Cannondale ST400',
     'activity': 'Repacked old rear hub; replaced cone — in effort to get knocking sound to go away',
     'cost': 54.44, 'shop': 'Bicycles NYC'},
    {'date': '2025-04-28', 'bike': 'Cannondale ST400',
     'activity': 'Swapped original wheels for new wheels again',
     'cost': 0.00, 'shop': ''},
    {'date': '2025-03-03', 'bike': 'Cannondale ST400',
     'activity': 'New wheel build: front rim with straight spokes; original front hub after accident (wanted butted spokes but used straight; took $40 off)',
     'cost': 207.14, 'shop': 'Bicycles NYC'},
    {'date': '2024-11-16', 'bike': 'Cannondale ST400',
     'activity': 'New bottom bracket — SUNLT SL26 68x127 SQ STL-CUP ENG',
     'cost': 54.99, 'shop': 'Bicycles NYC'},
    {'date': '2024-10-27', 'bike': 'Cannondale ST400',
     'activity': 'Swapped new wheels for original wheels with Vittoria tires',
     'cost': 0.00, 'shop': ''},
    {'date': '2024-09-07', 'bike': 'Cannondale ST400',
     'activity': 'Left pedal overhaul again — one side only had 10 balls (should have been 11)',
     'cost': 0.00, 'shop': ''},
    {'date': '2024-08-06', 'bike': 'Cannondale ST400',
     'activity': 'Panaracer Pasela Protite Urban/Touring Folding tires 27x1.25',
     'cost': 70.00, 'shop': 'Amazon'},
    {'date': '2024-07-13', 'bike': 'Cannondale ST400',
     'activity': 'Overhauled both pedals again (probably too early — maybe every 5k miles?)',
     'cost': 0.00, 'shop': ''},
    {'date': '2023-10-31', 'bike': 'Cannondale ST400',
     'activity': 'Vittoria Zaffiro Rigid Tires 27x1 1/8',
     'cost': 65.30, 'shop': 'Amazon'},
    {'date': '2023-10-09', 'bike': 'Cannondale ST400', 'activity': 'Velox wheel tape',
     'cost': 15.98, 'shop': 'Bicycles NYC'},
    {'date': '2023-10-09', 'bike': 'Cannondale ST400', 'activity': 'Rebuilt rear wheel true up',
     'cost': 32.00, 'shop': 'Bicycles NYC'},
    {'date': '2023-09-10', 'bike': 'Cannondale ST400',
     'activity': 'DT Swiss Competition Spokes for old rear wheel 296mm',
     'cost': 104.50, 'shop': 'Amazon'},
    {'date': '2023-08-10', 'bike': 'Cannondale ST400',
     'activity': 'New front and back wheels — too many spokes breaking; refused to rebuild wheels',
     'cost': 335.30, 'shop': 'Bicycles NYC'},
    {'date': '2023-07-16', 'bike': 'Cannondale ST400',
     'activity': 'Replace 1 spoke non-drive side rear wheel 296mm (only had them in black)',
     'cost': 34.84, 'shop': 'Bicycles NYC'},
    {'date': '2023-07-16', 'bike': 'Cannondale ST400', 'activity': 'Rotate tires',
     'cost': 0.00, 'shop': ''},
    {'date': '2023-07-13', 'bike': 'Cannondale ST400',
     'activity': 'New bike seat (already had 400 miles on it)',
     'cost': 90.00, 'shop': 'Torelli'},
    {'date': '2023-06-10', 'bike': 'Cannondale ST400',
     'activity': 'Overhauled both pedals; replaced balls in bearings',
     'cost': 0.00, 'shop': ''},
    {'date': '2023-05-21', 'bike': 'Cannondale ST400',
     'activity': 'Replace 2 spokes on front wheel and true it — front spokes are 300mm',
     'cost': 34.00, 'shop': 'Bicycles NYC'},
    {'date': '2023-04-30', 'bike': 'Cannondale ST400',
     'activity': 'Overhauled front wheel bearing; replaced 10 balls on right side',
     'cost': 0.00, 'shop': ''},
    {'date': '2023-03-05', 'bike': 'Cannondale ST400', 'activity': 'Ritchey seatpost 27.2mm 350mm',
     'cost': 40.99, 'shop': 'Performance'},
    {'date': '2023-02-11', 'bike': 'Cannondale ST400', 'activity': 'Headset replacement',
     'cost': 59.87, 'shop': 'Bicycles NYC'},
    {'date': '2022-10-24', 'bike': 'Cannondale ST400',
     'activity': 'True front and rear wheels; replace broken spoke in rear',
     'cost': 56.00, 'shop': 'Bicycles NYC'},
    {'date': '2022-10-22', 'bike': 'Cannondale ST400', 'activity': 'Zefal leather toe straps',
     'cost': 15.39, 'shop': 'Amazon'},
    {'date': '2021-06-27', 'bike': 'Cannondale ST400',
     'activity': 'Complete overhaul: new tires; new brake pads; new cables etc.',
     'cost': 504.02, 'shop': 'Pedals & Petals, Inlet NY'},
    {'date': '2021-06-01', 'bike': 'Cannondale ST400', 'activity': 'New bike seat',
     'cost': 88.58, 'shop': 'Torelli'},
    {'date': '1987-04-07', 'bike': 'Cannondale ST400', 'activity': 'Original purchase (estimated)',
     'cost': 500.00, 'shop': 'Bike World, Mount Kisco NY'},

    # --- Cannondale M700 ---
    {'date': '2025-06-24', 'bike': 'Cannondale M700',
     'activity': 'Mounting issue with new Schwalbe tire on new rear wheel',
     'cost': 32.60, 'shop': 'Master Bike Shop'},
    {'date': '2025-06-23', 'bike': 'Cannondale M700',
     'activity': 'Service (details not recorded)',
     'cost': 234.10, 'shop': 'Master Bike Shop'},
    {'date': '2025-06-23', 'bike': 'Cannondale M700',
     'activity': 'Schwalbe Hurricane RaceGuard Tires installed',
     'cost': 90.00, 'shop': 'Amazon Marketplace'},
    {'date': '2025-06-23', 'bike': 'Cannondale M700', 'activity': 'Ergon GP5 Handlebar Grips',
     'cost': 79.95, 'shop': 'REI'},
    {'date': '2025-04-06', 'bike': 'Cannondale M700',
     'activity': 'Replaced rear tire (Panaracer smoke) with Pisgah replacement',
     'cost': 0.00, 'shop': ''},
    {'date': '2025-04-06', 'bike': 'Cannondale M700',
     'activity': 'Rear wheel true up; fixed loose freewheel',
     'cost': 43.55, 'shop': 'Bicycles NYC'},
    {'date': '2024-12-07', 'bike': 'Cannondale M700', 'activity': 'New Sunlite water bottle cages',
     'cost': 21.76, 'shop': 'Amazon.com'},
    {'date': '2024-11-29', 'bike': 'Cannondale M700',
     'activity': 'Repacked rear Sachs hub bearings; replaced balls — front hub OK; does not require overhaul',
     'cost': 97.99, 'shop': 'Bicycles NYC'},
    {'date': '2024-11-24', 'bike': 'Cannondale M700',
     'activity': 'New Cateye Urban wireless bike computer',
     'cost': 44.95, 'shop': 'Amazon.com'},
    {'date': '2021-06-01', 'bike': 'Cannondale M700', 'activity': 'New bike seat',
     'cost': 88.58, 'shop': 'Torelli'},

    # --- Tommaso ---
    {'date': '2024-04-14', 'bike': 'Tommaso',
     'activity': 'New Vittoria Zaffiro Pro tires 700x25c',
     'cost': 71.84, 'shop': 'Amazon.com'},
    {'date': '2023-03-11', 'bike': 'Tommaso',
     'activity': 'New rear derailleur — Tiagra 4700 10s GS',
     'cost': 42.15, 'shop': 'Amazon.com'},
    {'date': '2023-03-11', 'bike': 'Tommaso', 'activity': 'New derailleur hanger',
     'cost': 20.00, 'shop': 'Tommasso'},
    {'date': '2023-03-11', 'bike': 'Tommaso', 'activity': 'New rear derailleur cable; install',
     'cost': 28.00, 'shop': 'Bicycles NYC'},
    {'date': '2023-03-11', 'bike': 'Tommaso', 'activity': 'New water bottle cage',
     'cost': 29.99, 'shop': 'Tommasso'},
    {'date': '2021-06-19', 'bike': 'Tommaso',
     'activity': 'New derailleur hanger; true rear wheel',
     'cost': 47.22, 'shop': 'Bicycles NYC'},
    {'date': '2021-05-31', 'bike': 'Tommaso',
     'activity': 'Adjust rear derailleur hanger (was bent)',
     'cost': 16.33, 'shop': 'Bicycles NYC'},
    {'date': '2021-05-16', 'bike': 'Tommaso',
     'activity': 'True front and rear wheels; replace spoke on front wheel',
     'cost': 48.99, 'shop': 'Bicycles NYC'},
    {'date': '2021-04-25', 'bike': 'Tommaso', 'activity': 'Sidi Genius 7 Road Shoes size 40.5',
     'cost': 249.99, 'shop': 'Performance Bike'},
    {'date': '2021-04-24', 'bike': 'Tommaso', 'activity': 'Speedplay Zero pedals stainless',
     'cost': 214.00, 'shop': 'REI'},
    {'date': '2020-06-07', 'bike': 'Tommaso',
     'activity': 'Original purchase; shipped to Pedals & Petals for assembly',
     'cost': 1187.99, 'shop': 'Amazon.com'},
]


def main():
    os.makedirs(MAINTENANCE_DIR, exist_ok=True)

    print(f"Importing {len(LEGACY_RECORDS)} legacy maintenance records...")

    rows = []
    for r in LEGACY_RECORDS:
        date_obj = datetime.strptime(r['date'], '%Y-%m-%d')
        date_str = date_obj.strftime('%-m/%-d/%Y')
        rows.append([date_str, r['bike'], r['activity'], f"{r['cost']:.2f}", r['shop']])

    rows.sort(key=lambda x: datetime.strptime(x[0], '%m/%d/%Y'), reverse=True)

    with open(MAINTENANCE_CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMNS)
        for row in rows:
            writer.writerow(row)

    print(f"Wrote {len(rows)} records to {MAINTENANCE_CSV}")


if __name__ == '__main__':
    main()
