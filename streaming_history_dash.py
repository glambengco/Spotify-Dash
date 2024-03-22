import pandas as pd
import plotly.express as px
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

# Set parameters for app UI
APP_THEME = dbc.themes.LUX
CHART_MARGIN = dict(t = 100, b = 100, l=100, r=40)
CHART_THEME = 'plotly_white'

# Read streaming history files and store into dataframe
def files_to_dataframe():
    json_list = []
    # Load my streaming history files from GitHub when deploying using render.com
    json_list.append('https://raw.githubusercontent.com/glambengco/Spotify-Dash/main/StreamingHistory_music_0.json')
    json_list.append('https://raw.githubusercontent.com/glambengco/Spotify-Dash/main/StreamingHistory_music_1.json')
    
    df_list = [pd.read_json(json_file) for json_file in json_list]
    df = pd.concat(df_list, axis = 0)

    df['endTime'] = pd.to_datetime(df['endTime'])
    
    # Get year and month values and store into separate columns
    df['year'] = df['endTime'].dt.year
    df['month'] = df['endTime'].dt.month
    df['monthName'] = df['endTime'].dt.strftime('%b')
    df['day'] = df['endTime'].dt.day

    return df

#-------------------- Unit conversion functions --------------------#
# Function to convert ms to minutes
def ms_to_min(ms):
    return ms/(1000*60)

# Function to convert ms to hours
def ms_to_hr(ms):
    return ms/(1000*60*60)

#-------------------- Grouping functions --------------------#
# Function to group by artist and calculate total msPlayed
def group_by_artist(df):
    return df.groupby('artistName')['msPlayed'].sum().reset_index()

# Function to group by track and calculate total msPlayed
def group_by_track(df):
    return df.groupby(['artistName', 'trackName'])['msPlayed'].sum().reset_index()

# Function to group by year and month and calculate total msPlayed
def group_by_year_month(df):
    return df.groupby(['year', 'month', 'monthName'])['msPlayed'].sum().reset_index()

# Function to group by day of week and calculate average msPlayed for each day of week
def group_by_day_of_week(df):
    df['date'] = pd.to_datetime(df['endTime'].dt.date)
    df_day = df.groupby('date')['msPlayed'].sum().reset_index()
    df_day['dayOfWeek'] = df_day['date'].dt.dayofweek
    df_day['dayName'] = df_day['date'].dt.strftime('%a')
    return df_day.groupby(['dayOfWeek', 'dayName'])['msPlayed'].mean().reset_index()

#-------------------- Filtering functions --------------------#
# Function to filter by month
def filter_by_month(df, year, month):
    return df[(df['year'] == year) & (df['month'] == month)]

#-------------------- Main plotting functions --------------------#
# Function to generate top artists chart
def top_artists_chart(df, n, chart_title):
    # Group by artists and get top n artists
    df = group_by_artist(df)
    df['minPlayed'] = ms_to_min(df['msPlayed'])
    df = df.sort_values('msPlayed').tail(n)
    
    # Generate bar chart
    fig = px.bar(df, x = 'minPlayed', y = 'artistName')
    fig.update_layout(title = chart_title,
                      xaxis_title = 'Total listening time (minutes)',
                      yaxis_title = '',
                      xaxis = dict(fixedrange = True),
                      yaxis = dict(tickmode = 'array',
                                   tickvals = df['artistName'],
                                   ticktext = df['artistName'].str.slice(0, 20) + '  ',
                                   fixedrange = True
                                   ),
                      margin = CHART_MARGIN,
                      template = CHART_THEME
                      )

    return dcc.Graph(figure = fig)

# Function to generate top songs chart
def top_songs_chart(df, n, chart_title, artist_label):
    # Group by track and get top n tracks
    df = group_by_track(df).sort_values('msPlayed').tail(n)
    df['minPlayed'] = ms_to_min(df['msPlayed'])
    df = df.sort_values('msPlayed').tail(n)
    
    # IF artist_abel set to true, artist anme of each track will be displayed in chart
    if artist_label == True:
        s = '<b>' + df['trackName'].str.slice(0, 20) + '</b>  <br>by ' + df['artistName'].str.slice(0, 20) + '  '
        artist_track = pd.Series(s)
        yaxis_format = dict(tickmode = 'array',
                            tickvals = df['trackName'],
                            ticktext = artist_track,
                            fixedrange = True
                           )
    else:
        yaxis_format = dict(ticksuffix = '  ', fixedrange = True)

    # Generate bar chart
    fig = px.bar(df, x = 'minPlayed', y = 'trackName') 
    fig.update_layout(title = chart_title,
                      xaxis_title = 'Total listening time (minutes)',
                      yaxis_title = '',
                      xaxis = dict(fixedrange = True),
                      yaxis = yaxis_format,
                      margin = CHART_MARGIN,
                      template = CHART_THEME
                      )

    return dcc.Graph(figure = fig)

# Function to generate monthly listening time chart
def time_chart(df, chart_title):
    # Group by year and month
    df = group_by_year_month(df)
    df['minPlayed'] = ms_to_min(df['msPlayed'])
    df['yearMonth'] = df['year'].astype(str) + '-' + df['month'].astype(str)

    # Generate month and year strings for x-axis tick labels
    xtick_labels = '<br>' + df['monthName'].astype(str) + '<br>' + df['year'].astype(str)

    # Generate line plot
    fig = px.line(df, x = 'yearMonth', y = 'minPlayed')
    fig.update_layout(title = chart_title,
                      xaxis_title = '',
                      yaxis_title = 'Total listening time (minutes)',
                      margin = CHART_MARGIN,
                      xaxis = dict(tickmode = 'array', 
                                   tickvals = df['yearMonth'][::2],
                                   ticktext = xtick_labels[::2],
                                   fixedrange = True
                                   ),
                      yaxis = dict(ticksuffix = '  ',
                                   range = (0, df['minPlayed'].max()*1.2),
                                   fixedrange = True
                                   ),
                      template = CHART_THEME
                      )

    return dcc.Graph(figure = fig)

# Function to generate average listening time by day of week
def time_by_day_of_week(df, chart_title):
    df_day_week = group_by_day_of_week(df)
    df_day_week['hrPlayed'] = ms_to_hr(df_day_week['msPlayed'])
    
    fig = px.bar(df_day_week, x = 'dayName', y = 'hrPlayed')
    fig.update_layout(title = chart_title, 
                      xaxis_title = '',
                      yaxis_title = 'Average listening time (hours)',
                      xaxis = dict(tickprefix = '<br>', 
                                   fixedrange = True
                                   ),
                      yaxis = dict(fixedrange = True,
                                   range = (0, df_day_week['hrPlayed'].max()*1.2)
                                   ),
                      margin = CHART_MARGIN,
                      template = CHART_THEME
                     )
    
    return dcc.Graph(figure = fig)

#-------------------- Monthly plotting functions --------------------#
# Function to generate top artists chart on a given month
def top_artists_of_month(df, n, year, month):
    df_month = filter_by_month(df, year, month)
    year_month = pd.to_datetime(str(year) + '-' + str(month))
    chart_title = 'Top {} Artists of {}'.format(n, year_month.strftime('%B %Y'))
    
    return top_artists_chart(df_month, n, chart_title)

# Function to generate top artists chart on a given month
def top_songs_of_month(df, n, year, month):
    df_month = filter_by_month(df, year, month)
    year_month = pd.to_datetime(str(year) + '-' + str(month))
    chart_title = 'Top {} Songs of {}'.format(n, year_month.strftime('%B %Y'))
    
    return top_songs_chart(df_month, n, chart_title, artist_label=True)

# Function to generate average listening time by day of week on a given month
def time_by_day_of_week_on_month(df, year, month):
    df_month = filter_by_month(df, year, month)
    year_month = pd.to_datetime(str(year) + '-' + str(month))
    chart_title = 'Average Listening Time by Day of Week <br>on {}'.format(year_month.strftime('%B %Y'))
    
    return time_by_day_of_week(df_month, chart_title)

#-------------------- Loading data --------------------#
# Load streaming history data into dataframe
streaming_history = files_to_dataframe()

#-------------------- Dash app --------------------#
# Initialize Dash app
app = dash.Dash(__name__,
                # meta tags for responsive web layout
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0, maximum-scale=3.0, minimum-scale=0.5,'
                            }
                           ],
                # Set theme
                external_stylesheets = [APP_THEME]
                )
# Use when deploying in render.com
server = app.server

#-------------------- Variables for app layout --------------------#
# Variables for app title
app_title = 'Spotify Streaming History Dashboard'

# Dropdown menu options and style for choosing visualization
dropdown_label = 'Select month to analyze'

# First element is option to select all data
dropdown_options = [{'label': 'Select all data', 'value': 'all'}]

# Generate strings for dropdown options to filter by month
monthly_data = group_by_year_month(streaming_history)
year_month = pd.to_datetime(monthly_data['year'].astype(str) + '-' + monthly_data['month'].astype(str))
for m in year_month:
    option = {'label': m.strftime('%B %Y'), 'value': m.strftime('%Y %m')}
    dropdown_options.append(option)

# Title style
title_style = {'textAlign': 'center',
               'font-size': 28,
               'margin-top': '20px',
               'width': '100%'
               }

# Dropdown menu Div style
dropdown_div_style = {'width': '90%', 
                  'max-width': '1080px', 
                  'margin': 'auto',
                  'margin-top': '20px',
                  'margin-bottom': '20px',
                  'font-size': 20
                  }

# Dropdown style
dropdown_style = {'background': 'transparent'}

# Output style
output_style = {'margin': 'auto',
                'max-width': '100%'
                }

# Chart style
chart_display = {'display': 'flex',
                 'flex-direction': 'row',
                 'flex-wrap': 'wrap',
                 'justify-content': 'center',
                 'margin': 'auto',
                 'max-width': '100%'
                 }

# Graph style
graph_style = {'max-width': '100%'}

#-------------------- Variables for app layout --------------------#
app.layout = html.Div([html.H1(app_title, 
                               style = title_style
                               ), 
                       html.Label('by Gillano Lambengco'),
                       html.A('Link to GitHub repo', 
                              href = 'https://github.com/glambengco/Spotify-Dash/tree/main'
                              ),
                       # Div for dropdown menu
                       html.Div([html.Label(dropdown_label),
                                 dcc.Dropdown(id = 'dropdown-month',
                                              options = dropdown_options,
                                              placeholder = 'Select month',
                                              value = 'Select month',
                                              style = dropdown_style
                                              )
                                 ], 
                                style = dropdown_div_style
                                ),
                       # Div for output charts
                       html.Div(id = 'output-container', 
                                className = 'chart-grid', 
                                style = output_style
                                )
                       ]
                      )


#-------------------- Callback function --------------------#
@app.callback(Output(component_id = 'output-container', component_property = 'children'),
              Input(component_id = 'dropdown-month', component_property = 'value')
              )

def update_output_container(input_month):
    if input_month == 'all':
        n = 5
        chart_title_1 = 'Top {} Most Played Artists on Spotify'.format(n)
        chart_title_2 = 'Top {} Most Played Songs on Spotify'.format(n)
        chart_title_3 = 'Monthly Listening Time'
        chart_title_4 = 'Average Listening Time by Day of Week'

        chart_1 = top_artists_chart(streaming_history, n, chart_title_1)
        chart_2 = top_songs_chart(streaming_history, n, chart_title_2, artist_label=True)
        chart_3 = time_chart(streaming_history, chart_title_3),
        chart_4 = time_by_day_of_week(streaming_history, chart_title_4)

        return html.Div(className='chart-item', 
                        children=[html.Div(chart_1, style = graph_style),
                                  html.Div(chart_2, style = graph_style),
                                  html.Div(chart_3, style = graph_style),
                                  html.Div(chart_4, style = graph_style)
                                 ],
                        style=chart_display
                       )
    
    elif input_month != 'Select month': 
        i = str(input_month)
        year = int(i.split()[0])
        month = int(i.split()[1])
        n = 5
        
        chart_1 = top_artists_of_month(streaming_history, n, year, month)
        chart_2 = top_songs_of_month(streaming_history, n, year, month)
        chart_3 = time_by_day_of_week_on_month(streaming_history, year, month)

        return html.Div(className = 'chart-item', 
                        children=[html.Div(chart_1, style = graph_style),
                                  html.Div(chart_2, style = graph_style),
                                  html.Div(chart_3, style = graph_style)
                                 ],
                        style= chart_display
                       )

    else:
        return None

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)
