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
MAINTENANCE_CSV = "/Users/chris/git/darringer-bikelog/data/maintenance/maintenance.csv"
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
        dfs.append(df)

    df = pd.concat(dfs, ignore_index=True)

    # Parse dates; coerce malformed rows (e.g. repeated headers) to NaT
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y', errors='coerce')
    df = df.dropna(subset=['Date'])
    df['Distance'] = pd.to_numeric(df['Distance'], errors='coerce')
    df = df.dropna(subset=['Distance'])

    df['Year'] = df['Date'].dt.year.astype(int)
    return df


def load_maintenance():
    """Load maintenance CSV into a DataFrame."""
    path = Path(MAINTENANCE_CSV)
    if not path.exists():
        return pd.DataFrame(columns=['Date', 'Bike', 'Activity', 'Cost', 'Shop'])
    df = pd.read_csv(path)
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y', errors='coerce')
    df = df.dropna(subset=['Date'])
    df['Cost'] = pd.to_numeric(df['Cost'], errors='coerce').fillna(0)
    return df


def build_cost_by_bike_chart(mdf):
    """Horizontal bar chart of total maintenance cost per bike."""
    totals = mdf.groupby('Bike')['Cost'].sum().sort_values(ascending=True)
    totals = totals[totals > 0]

    fig = go.Figure(go.Bar(
        x=totals.values,
        y=totals.index,
        orientation='h',
        text=[f'${v:,.0f}' for v in totals.values],
        textposition='outside',
        marker_color='#e07b39',
        hovertemplate='%{y}: $%{x:,.0f}<extra></extra>'
    ))
    fig.update_layout(
        title='Total Maintenance Cost by Bike',
        xaxis_title='Total Cost ($)',
        xaxis=dict(tickprefix='$'),
        margin=dict(l=160, r=80),
    )
    return fig


def build_cumulative_cost_chart(mdf):
    """Cumulative maintenance cost over time, one line per bike."""
    bikes_with_cost = mdf.groupby('Bike')['Cost'].sum()
    bikes_with_cost = bikes_with_cost[bikes_with_cost > 0].index.tolist()

    fig = go.Figure()
    for bike in sorted(bikes_with_cost):
        bike_df = mdf[mdf['Bike'] == bike].sort_values('Date')
        cumulative = bike_df['Cost'].cumsum()
        fig.add_trace(go.Scatter(
            x=bike_df['Date'],
            y=cumulative,
            mode='lines+markers',
            name=bike,
            hovertemplate='%{x|%b %d, %Y}: $%{y:,.0f}<extra>' + bike + '</extra>'
        ))

    fig.update_layout(
        title='Cumulative Maintenance Cost by Bike',
        xaxis_title='Date',
        yaxis_title='Cumulative Cost ($)',
        yaxis=dict(tickprefix='$'),
        hovermode='x unified',
        legend_title='Bike'
    )
    return fig


def build_cost_per_mile_chart(mdf, rides_df):
    """Bar chart of maintenance cost per tracked mile, per bike."""
    total_cost = mdf.groupby('Bike')['Cost'].sum()
    total_cost = total_cost[total_cost > 0]
    total_miles = rides_df.groupby('Bike')['Distance'].sum()

    common = total_cost.index.intersection(total_miles.index)
    common = [b for b in common if total_miles[b] > 0]

    cpm = pd.Series(
        {bike: total_cost[bike] / total_miles[bike] for bike in common}
    ).sort_values(ascending=False)

    fig = go.Figure(go.Bar(
        x=cpm.index,
        y=cpm.values,
        text=[f'${v:.2f}' for v in cpm.values],
        textposition='outside',
        marker_color='#e07b39',
        hovertemplate='%{x}: $%{y:.2f}/mi<extra></extra>'
    ))
    fig.update_layout(
        title='Maintenance Cost per Mile by Bike<br>'
              '<sup>Based on miles tracked in ride log only — lifetime mileage may be higher for some bikes</sup>',
        xaxis_title='Bike',
        yaxis_title='Cost per Mile ($)',
        yaxis=dict(tickprefix='$'),
        xaxis_tickangle=-30,
        margin=dict(t=80)
    )
    return fig


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
    """Generate a self-contained HTML report with ride and cost-of-ownership charts."""
    print("Loading ride data...")
    df = load_all_rides()

    print("Loading maintenance data...")
    mdf = load_maintenance()

    print("Building charts...")
    cumulative_fig = build_cumulative_chart(df, year)
    yoy_fig = build_yoy_table(df)
    bike_fig = build_bike_chart(df)
    cost_by_bike_fig = build_cost_by_bike_chart(mdf)
    cumulative_cost_fig = build_cumulative_cost_chart(mdf)
    cost_per_mile_fig = build_cost_per_mile_chart(mdf, df)

    # Embed Plotly JS once; each chart div uses include_plotlyjs=False
    plotlyjs = plotly.offline.get_plotlyjs()
    cumulative_div = cumulative_fig.to_html(full_html=False, include_plotlyjs=False)
    yoy_div = yoy_fig.to_html(full_html=False, include_plotlyjs=False)
    bike_div = bike_fig.to_html(full_html=False, include_plotlyjs=False)
    cost_by_bike_div = cost_by_bike_fig.to_html(full_html=False, include_plotlyjs=False)
    cumulative_cost_div = cumulative_cost_fig.to_html(full_html=False, include_plotlyjs=False)
    cost_per_mile_div = cost_per_mile_fig.to_html(full_html=False, include_plotlyjs=False)

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
    .generated {{ color: #999; font-size: 0.85rem; margin-bottom: 1.5rem; }}
    .chart {{ background: white; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); padding: 0.5rem; margin-bottom: 2rem; }}
    .tab-bar {{ display: flex; border-bottom: 2px solid #4a7fc1; margin-bottom: 1.5rem; }}
    .tab-btn {{
      padding: 0.55rem 1.4rem; cursor: pointer; font-size: 0.95rem; color: #555;
      background: #eef2f8; border: 1px solid #ccd6e8; border-bottom: none;
      border-radius: 6px 6px 0 0; margin-right: 4px; margin-bottom: -2px;
    }}
    .tab-btn:hover {{ background: #dde6f5; }}
    .tab-btn.active {{ background: #4a7fc1; color: white; border-color: #4a7fc1; }}
    .tab-content {{ display: none; }}
    .tab-content.active {{ display: block; }}
  </style>
  <script>{plotlyjs}</script>
</head>
<body>
  <h1>Darringer Family Bike Log — {year}</h1>
  <p class="generated">Generated {timestamp}</p>

  <div class="tab-bar">
    <button class="tab-btn active" onclick="switchTab(event, 'rides')">Ride Metrics</button>
    <button class="tab-btn" onclick="switchTab(event, 'costs')">Cost of Ownership</button>
  </div>

  <div id="rides" class="tab-content active">
    <div class="chart">{cumulative_div}</div>
    <div class="chart">{yoy_div}</div>
    <div class="chart">{bike_div}</div>
  </div>

  <div id="costs" class="tab-content">
    <div class="chart">{cost_by_bike_div}</div>
    <div class="chart">{cumulative_cost_div}</div>
    <div class="chart">{cost_per_mile_div}</div>
  </div>

  <script>
  function switchTab(event, tabId) {{
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
    event.currentTarget.classList.add('active');
    window.dispatchEvent(new Event('resize'));
  }}
  </script>
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
