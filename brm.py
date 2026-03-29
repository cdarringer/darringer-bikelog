#!/usr/bin/env python3
"""
Bike Ride Metrics

Generates an interactive HTML report with charts for local viewing and S3 publishing.
"""

import argparse
import os
import webbrowser
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.offline

CSV_DIR = "/Users/chris/git/darringer-bikelog/data/rides"
OUTPUT_HTML = os.path.join(CSV_DIR, "bikelog.html")
ACTIVE_RIDERS = ["Chris", "Sally", "Theo", "Lucja", "Frances"]


def load_all_rides():
    """Load and concatenate all year CSV files into a single DataFrame."""
    csv_files = sorted(Path(CSV_DIR).glob('rides_[0-9]*.csv'))
    if not csv_files:
        raise FileNotFoundError(f"No ride CSV files found in {CSV_DIR}")

    dfs = []
    for path in csv_files:
        df = pd.read_csv(path)
        # Normalize column name inconsistency across historical files
        df.rename(columns={'Comments': 'Comment'}, inplace=True)
        dfs.append(df)

    df = pd.concat(dfs, ignore_index=True)

    # Parse dates; coerce malformed rows (e.g. repeated headers) to NaT
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y', errors='coerce')
    df = df.dropna(subset=['Date'])
    df['Distance'] = pd.to_numeric(df['Distance'], errors='coerce')
    df = df.dropna(subset=['Distance'])

    df['Year'] = df['Date'].dt.year.astype(int)
    return df


def build_cumulative_chart(df, year):
    """Cumulative mileage line chart per rider — toggleable between current year and all time."""
    year_df = df[df['Year'] == year].copy()
    today = datetime.now().date()
    fig = go.Figure()

    # Current year traces (visible by default)
    for rider in ACTIVE_RIDERS:
        rider_df = year_df[year_df['Name'] == rider].sort_values('Date')
        if rider_df.empty:
            continue
        cumulative = rider_df['Distance'].cumsum()
        fig.add_trace(go.Scatter(
            x=rider_df['Date'],
            y=cumulative,
            mode='lines+markers',
            name=rider,
            legendgroup=rider,
            visible=True,
            hovertemplate='%{x|%b %d}: %{y:.0f} mi<extra>' + rider + '</extra>'
        ))

    n_current = len(fig.data)

    # All-time traces (hidden by default)
    for rider in ACTIVE_RIDERS:
        rider_df = df[df['Name'] == rider].sort_values('Date')
        if rider_df.empty:
            continue
        cumulative = rider_df['Distance'].cumsum()
        fig.add_trace(go.Scatter(
            x=rider_df['Date'],
            y=cumulative,
            mode='lines',
            name=rider,
            legendgroup=rider,
            showlegend=False,
            visible=False,
            hovertemplate='%{x|%b %d, %Y}: %{y:,.0f} mi<extra>' + rider + '</extra>'
        ))

    n_alltime = len(fig.data) - n_current

    fig.add_vline(
        x=pd.Timestamp(today).value / 1e6,
        line_dash='dash',
        line_color='gray',
        annotation_text='Today',
        annotation_position='top right'
    )

    current_vis = [True] * n_current + [False] * n_alltime
    alltime_vis = [False] * n_current + [True] * n_alltime

    fig.update_layout(
        title=f'{year} Cumulative Miles by Rider',
        xaxis_title='Date',
        yaxis_title='Cumulative Miles',
        hovermode='x unified',
        legend_title='Rider',
        updatemenus=[dict(
            type='buttons',
            direction='right',
            x=0.0,
            y=1.12,
            xanchor='left',
            buttons=[
                dict(
                    label='Current Year',
                    method='update',
                    args=[
                        {'visible': current_vis},
                        {'title': f'{year} Cumulative Miles by Rider'}
                    ]
                ),
                dict(
                    label='All Time',
                    method='update',
                    args=[
                        {'visible': alltime_vis},
                        {'title': 'All-Time Cumulative Miles by Rider'}
                    ]
                ),
            ],
            active=0
        )]
    )
    return fig


def build_bike_chart(df):
    """Stacked bar chart of all-time mileage by bike, broken down by rider."""
    year_df = df[df['Name'].isin(ACTIVE_RIDERS)].copy()
    pivot = year_df.groupby(['Bike', 'Name'])['Distance'].sum().reset_index()

    # Sort bikes by total mileage descending
    bike_order = (
        pivot.groupby('Bike')['Distance'].sum()
        .sort_values(ascending=False)
        .index.tolist()
    )

    totals = pivot.groupby('Bike')['Distance'].sum()

    fig = go.Figure()
    for rider in ACTIVE_RIDERS:
        rider_data = pivot[pivot['Name'] == rider].set_index('Bike')
        y_vals = [rider_data.loc[bike, 'Distance'] if bike in rider_data.index else 0
                  for bike in bike_order]
        if sum(y_vals) == 0:
            continue
        fig.add_trace(go.Bar(
            x=bike_order,
            y=y_vals,
            name=rider
        ))

    # Total labels at the top of each stacked bar
    fig.add_trace(go.Scatter(
        x=bike_order,
        y=[totals[bike] for bike in bike_order],
        mode='text',
        text=[f'{round(totals[bike]):,}' for bike in bike_order],
        textposition='top center',
        showlegend=False,
        hoverinfo='skip'
    ))

    fig.update_layout(
        barmode='stack',
        title='All-Time Miles by Bike',
        xaxis_title='Bike',
        yaxis_title='Miles',
        xaxis_tickangle=-30,
        legend_title='Rider'
    )
    return fig


def _pct_to_color(pct):
    """Map a YoY percentage to a red-white-green background color."""
    if pct is None:
        return 'rgb(240,240,240)'
    cap = 30.0
    ratio = max(-1.0, min(1.0, pct / cap))
    if ratio >= 0:
        r = int(255 * (1 - ratio * 0.65))
        g = 255
        b = int(255 * (1 - ratio * 0.65))
    else:
        ratio = abs(ratio)
        r = 255
        g = int(255 * (1 - ratio * 0.65))
        b = int(255 * (1 - ratio * 0.65))
    return f'rgb({r},{g},{b})'


def build_yoy_table(df):
    """Table of annual mileage per rider with YoY% heatmap coloring."""
    active_df = df[df['Name'].isin(ACTIVE_RIDERS)]
    # pivot: index=Year, columns=Rider
    yearly = (
        active_df.groupby(['Year', 'Name'])['Distance']
        .sum()
        .unstack(fill_value=0)
    )
    years = sorted(yearly.index.tolist())

    # Only include riders who have any data
    riders = [r for r in ACTIVE_RIDERS if r in yearly.columns and yearly[r].sum() > 0]

    # Build column data: one column per year, one row per rider
    year_cell_values = []   # list of lists (one per year column)
    year_cell_colors = []   # list of lists (one per year column)

    for i, yr in enumerate(years):
        col_vals = []
        col_colors = []
        prev_yr = years[i - 1] if i > 0 else None
        for rider in riders:
            miles = yearly.loc[yr, rider] if yr in yearly.index and rider in yearly.columns else 0
            prev_miles = (
                yearly.loc[prev_yr, rider]
                if prev_yr and prev_yr in yearly.index and rider in yearly.columns
                else 0
            )
            if miles == 0:
                col_vals.append('')
                col_colors.append('rgb(250,250,250)')
            elif prev_miles == 0:
                col_vals.append(f'{miles:,.0f}')
                col_colors.append('rgb(240,240,240)')
            else:
                pct = (miles - prev_miles) / prev_miles * 100
                col_vals.append(f'{miles:,.0f}<br>{pct:+.0f}%')
                col_colors.append(_pct_to_color(pct))
        year_cell_values.append(col_vals)
        year_cell_colors.append(col_colors)

    n_riders = len(riders)
    fig = go.Figure(data=[go.Table(
        columnwidth=[80] + [60] * len(years),
        header=dict(
            values=['<b>Rider</b>'] + [f'<b>{yr}</b>' for yr in years],
            fill_color='#4a7fc1',
            font=dict(color='white', size=12),
            align='center',
            height=32
        ),
        cells=dict(
            values=[riders] + year_cell_values,
            fill_color=[['rgb(245,245,245)'] * n_riders] + year_cell_colors,
            align=['left'] + ['center'] * len(years),
            font=dict(size=11),
            height=36
        )
    )])

    fig.update_layout(
        title='Annual Miles by Rider — All Years<br>'
              '<sup>Cell color: green = improvement vs prior year, red = decline (capped at ±30%)</sup>',
        margin=dict(t=80)
    )
    return fig


def build_report(year):
    """Generate a self-contained HTML report with all three charts."""
    print("Loading ride data...")
    df = load_all_rides()

    print("Building charts...")
    cumulative_fig = build_cumulative_chart(df, year)
    yoy_fig = build_yoy_table(df)
    bike_fig = build_bike_chart(df)

    # Embed Plotly JS once; each chart div uses include_plotlyjs=False
    plotlyjs = plotly.offline.get_plotlyjs()
    cumulative_div = cumulative_fig.to_html(full_html=False, include_plotlyjs=False)
    yoy_div = yoy_fig.to_html(full_html=False, include_plotlyjs=False)
    bike_div = bike_fig.to_html(full_html=False, include_plotlyjs=False)

    timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Darringer Bike Log — {year} Metrics</title>
  <style>
    body {{ font-family: sans-serif; max-width: 1200px; margin: 0 auto; padding: 1rem 2rem; background: #fafafa; }}
    h1 {{ color: #333; margin-bottom: 0.25rem; }}
    .generated {{ color: #999; font-size: 0.85rem; margin-bottom: 2rem; }}
    .chart {{ background: white; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); padding: 0.5rem; margin-bottom: 2rem; }}
  </style>
  <script>{plotlyjs}</script>
</head>
<body>
  <h1>Darringer Family Bike Log — {year}</h1>
  <p class="generated">Generated {timestamp}</p>
  <div class="chart">{cumulative_div}</div>
  <div class="chart">{yoy_div}</div>
  <div class="chart">{bike_div}</div>
</body>
</html>"""
    return html


def main():
    parser = argparse.ArgumentParser(
        description='Generate bike ride metrics HTML report'
    )
    parser.add_argument(
        '--year',
        type=int,
        default=datetime.now().year,
        help='Year for current-year charts (default: current year)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=OUTPUT_HTML,
        help=f'Output HTML file path (default: {OUTPUT_HTML})'
    )
    parser.add_argument(
        '--no-open',
        action='store_true',
        help='Do not automatically open the report in a browser'
    )
    args = parser.parse_args()

    html = build_report(args.year)

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Report written to {args.output}")

    if not args.no_open:
        webbrowser.open(f'file://{os.path.abspath(args.output)}')
        print("Opening in browser...")


if __name__ == '__main__':
    main()
