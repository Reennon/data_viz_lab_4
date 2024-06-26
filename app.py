# region Imports
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
# endregion
# region Data Ingestion
# Load your dataset
df = pd.read_csv("/home/reennon/data/all_month.csv")
df['time'] = pd.to_datetime(df['time'])
df['date'] = df['time'].dt.date
# Clip mag size to draw the size of the earthquake on a plot (cannot be negative on plot)
df['mag_size'] = df['mag'].clip(0.1)
# register App
app = dash.Dash(__name__)
# define app layout
app.layout = html.Div([
    dcc.Graph(id='map-plot', config={'scrollZoom': False}),
    dcc.Graph(id='time-series-plot'),
    dcc.Graph(id='magnitude-distribution-plot')
])

@app.callback(
    [
        Output('map-plot', 'figure'),
        Output('time-series-plot', 'figure')
    ],
    [
        Input('magnitude-distribution-plot', 'selectedData'),
        Input('time-series-plot', 'relayoutData')
    ]
)
def update_map_and_time_series(selectedMagData, selectedTimeData):
    filtered_df = df

    # Handle time range selection from the time-series plot
    if selectedTimeData and 'xaxis.range[0]' in selectedTimeData:
        start_date = pd.to_datetime(selectedTimeData['xaxis.range[0]']).date()
        end_date = pd.to_datetime(selectedTimeData['xaxis.range[1]']).date()
        filtered_df = filtered_df[(df['date'] >= start_date) & (df['date'] <= end_date)]

    # Handle magnitude selection from the magnitude distribution plot
    if selectedMagData:
        selected_mags = [point['x'] for point in selectedMagData['points']]
        filtered_df = filtered_df[df['mag'].isin(selected_mags)]

    # Update map
    map_fig = px.scatter_geo(
        filtered_df,
        height=900,
        lat='latitude',
        lon='longitude',
        color='mag',
        hover_name='place',
        size='mag_size',
        projection='natural earth',
        title='Map of Earthquakes'
    )
    map_fig.layout.template = 'plotly_dark'
    map_fig.layout.xaxis.fixedrange = False
    map_fig.layout.yaxis.fixedrange = False

    # Update time series plot
    time_series_fig = px.line(
        filtered_df.groupby('date').size().reset_index(name='count'),
        x='date',
        y='count',
        title='Number of Earthquakes Over Time'
    )
    time_series_fig.layout.template = 'plotly_dark'

    return map_fig, time_series_fig

@app.callback(
    Output('magnitude-distribution-plot', 'figure'),
    [Input('map-plot', 'selectedData')]
)
def update_magnitude_distribution(selectedData):
    if selectedData:
        points = selectedData['points']
        lats = [point['lat'] for point in points]
        lons = [point['lon'] for point in points]
        filtered_df = df[df['latitude'].isin(lats) & df['longitude'].isin(lons)]
    else:
        filtered_df = df

    mag_dist_fig = px.histogram(
        filtered_df,
        x='mag',
        nbins=40,
        title='Distribution of Earthquake Magnitudes'
    )
    mag_dist_fig.layout.template = 'plotly_dark'

    return mag_dist_fig

if __name__ == '__main__':
    app.run_server(debug=True)
