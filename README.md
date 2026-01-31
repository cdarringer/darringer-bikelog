# darringer-bikelog

A simple command-line utility for tracking bike rides.

## Features

- Record bike rides with date, rider, distance, and bike type
- Automatic CSV file organization by year (rides_YYYY.csv)
- Default value for date (today)
- Select rider from a predefined list
- Select bike from a predefined list

## Getting Started

No dependencies required! This utility uses only Python standard library.

### Using the `brb` Command

A `brb` wrapper script is included for convenience. You can use it in two ways:

**Option 1: Run from the project directory**
```bash
./brb --rider "Chris" --distance 15 --bike "Cannondale ST400"
```

**Option 2: Make it available system-wide**

Add the project directory to your PATH by adding this line to your `~/.bashrc` or `~/.zshrc`:
```bash
export PATH="$PATH:/Users/chris/git/darringer-bikelog"
```

Then reload your shell:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

Now you can use `brb` from anywhere:
```bash
brb --rider "Chris" --distance 15 --bike "Cannondale ST400"
```

### Usage

Log a bike ride:
```bash
python bikelog.py --rider "Chris" --distance 15 --bike "Cannondale ST400"
# or
brb --rider "Chris" --distance 15 --bike "Cannondale ST400"
```

With custom date:
```bash
python bikelog.py --date 2024-01-15 --rider "Chris" --distance 20 --bike "Cannondale ST400"
# or
brb --date 2024-01-15 --rider "Chris" --distance 20 --bike "Cannondale ST400"
```

List available bikes:
```bash
python bikelog.py --list-bikes
# or
brb --list-bikes
```

List available riders:
```bash
python bikelog.py --list-riders
# or
brb --list-riders
```

### Command-Line Options

- `--date` (optional): Date of the ride in YYYY-MM-DD format. Defaults to today.
- `--rider` (required): Rider name. Use `--list-riders` to see available options.
- `--distance` (required): Distance of the ride in miles.
- `--bike` (required): Bike used for the ride. Use `--list-bikes` to see available options.
- `--list-bikes`: Display all available bike options and exit.
- `--list-riders`: Display all available rider options and exit.

### Data Storage

Rides are stored in CSV files organized by year in the `rides/` directory:
- `rides/rides_2024.csv` for 2024 rides
- `rides/rides_2025.csv` for 2025 rides
- etc.

Each CSV file contains columns: Date, Name, Distance, Bike

## Contributing

Contributions are welcome! Please open issues or submit pull requests.

## License

This project is licensed under the MIT License.