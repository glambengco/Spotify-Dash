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
px.defaults.template = "plotly"

# Read streaming history files and store into dataframe
def files_to_dataframe():
    # Uncomment below to load streaming history files from local machine
    # files = os.listdir('./')
    # json_list = [f for f in files if f.startswith('StreamingHistory_music')]

    # Load streaming history files from GitHub when deploying using render.com
    # Replace with your own files
    json_list = []
    json_list.append('https://raw.githubusercontent.com/glambengco/Spotify-Dash/main/StreamingHistory_music_0.json')
    json_list.append('https://raw.githubusercontent.com/glambengco/Spotify-Dash/main/StreamingHistory_music_1.json')
    
    df_list = [pd.read_json(json_file) for json_file in json_list]
    df = pd.concat(df_list, axis = 0)

    df['endTime'] = pd.to_datetime(df['endTime'])
    
    # Get year and month values and store into separate columns
    df['date'] = pd.to_datetime(df['endTime'].dt.date)
    df['year'] = df['endTime'].dt.year
    df['month'] = df['endTime'].dt.month
    df['monthName'] = df['endTime'].dt.strftime('%b')
    df['dayOfWeek'] = df['endTime'].dt.dayofweek
    df['dayName'] = df['endTime'].dt.strftime('%a')
    df['hour'] = df['endTime'].dt.hour

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

# Function to group by day of week and calculate average msPlayed
def group_by_day_of_week(df):
    df_day = df.groupby('date')['msPlayed'].sum().reset_index()
    df_day['dayOfWeek'] = df_day['date'].dt.dayofweek
    df_day['dayName'] = df_day['date'].dt.strftime('%a')
    return df_day.groupby(['dayOfWeek', 'dayName'])['msPlayed'].mean().reset_index()

# Function to group by weekday or weekend
def group_by_weekday_weekend(df):
    df['weekend'] = df['dayOfWeek'] > 4
    return df.groupby('weekend')['msPlayed'].sum().reset_index()

# Function to group by hour and calculate average msPlayed
def group_by_hour(df):
    df['hour_12'] = df['endTime'].dt.strftime('%I %p')
    df_day_hour = df.groupby(['date', 'hour', 'hour_12'])['msPlayed'].sum().reset_index()
    return df_day_hour.groupby(['hour', 'hour_12'])['msPlayed'].mean().reset_index()

# Function to group by artist
def group_by_artist(df):
    return df.groupby('artistName')['msPlayed'].sum().reset_index()

# Function to group by track
def group_by_track(df):
    return df.groupby(['artistName', 'trackName'])['msPlayed'].sum().reset_index()

#-------------------- Filtering functions --------------------#
# Function to filter by month
def filter_by_month(df, year, month):
    return df[(df['year'] == year) & (df['month'] == month)]

#-------------------- Main plotting functions --------------------#

# Function to plot total listening time by month
def time_by_month(df):
    # Group by year and month
    df = group_by_year_month(df)
    df['minPlayed'] = ms_to_min(df['msPlayed'])
    df['yearMonth'] = df['year'].astype(str) + '-' + df['month'].astype(str)

    # Generate month and year strings for x-axis tick labels
    xtick_labels = '<br>' + df['monthName'].astype(str) + '<br>' + df['year'].astype(str)

    # Generate line chart
    fig = px.line(df, x = 'yearMonth', y = 'minPlayed')
    fig.update_layout(title = 'Total Listening Time by Month',
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
                                   )
                      )
    return fig

# Function to plot average listening time by day of week
def time_by_day_of_week(df):
    # Group by day of week
    df_day_week = group_by_day_of_week(df)
    df_day_week['hrPlayed'] = ms_to_hr(df_day_week['msPlayed'])

    # Generate bar chart
    fig = px.bar(df_day_week, x = 'dayName', y = 'hrPlayed')
    fig.update_layout(title = 'Average Listening Time by Day of Week', 
                      xaxis_title = '',
                      yaxis_title = 'Average listening time (hours)',
                      xaxis = dict(tickprefix = '<br>', 
                                   fixedrange = True
                                   ),
                      yaxis = dict(fixedrange = True,
                                   range = (0, df_day_week['hrPlayed'].max()*1.2)
                                   ),
                      margin = CHART_MARGIN
                     )
    
    return fig

# Function to plot total listening time by wekday or weekend
def time_by_weekday_weekend(df):
    # Group by weekday or weekend
    df_weekday_weekend = group_by_weekday_weekend(df)
    df_weekday_weekend['hrPlayed'] = ms_to_hr(df_weekday_weekend['msPlayed'])

    # Generate pie chart
    fig = px.pie(df_weekday_weekend, 
                 names = ['Weekday', 'Weekend'], 
                 values = 'hrPlayed'
                 )
    fig.update_traces(textposition = 'inside', 
                      textinfo = 'percent+label',
                      )
    fig.update_layout(title = 'Total Listening Time<br>by Weekday vs. Weekend',
                      margin = CHART_MARGIN,
                      showlegend = False
                      )
    
    return fig

# Function to plot average listening time by hour
def time_by_hour(df):
    # Group by hour
    df_hour = group_by_hour(df)
    df_hour['minPlayed'] = ms_to_min(df_hour['msPlayed'])

    # Generate strings for x-axis tick labels
    xtick_labels = pd.Series(['12<br>AM', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', 
                              '12<br>PM', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11'
                              ]
                             )
    
    # Generate bar chart
    fig = px.bar(df_hour, x = 'hour', y = 'minPlayed')
    fig.update_layout(title = 'Average Listening Time by Hour', 
                      xaxis_title = '',
                      yaxis_title = 'Average listening time (minutes)',
                      xaxis = dict(tickmode = 'array', 
                                   tickvals = df_hour['hour'][::3],
                                   ticktext = xtick_labels[::3],
                                   fixedrange = True
                                   ),
                      yaxis = dict(fixedrange = True,
                                   range = (0, df_hour['minPlayed'].max()*1.2)
                                   ),
                      margin = CHART_MARGIN
                      )
    
    return fig

# Function to plot top artists
def top_artists_chart(df, n):
    # Group by artists and get top n artists
    df = group_by_artist(df)
    df['minPlayed'] = ms_to_min(df['msPlayed'])
    df = df.sort_values('msPlayed').tail(n)
    
    # Generate bar chart
    fig = px.bar(df, x = 'minPlayed', y = 'artistName')
    fig.update_layout(title = 'Top {} Most Played Artists'.format(n),
                      xaxis_title = 'Total listening time (minutes)',
                      yaxis_title = '',
                      xaxis = dict(ticksuffix = '  ', 
                                   fixedrange = True
                                   ),
                      yaxis = dict(tickmode = 'array',
                                   tickvals = df['artistName'],
                                   ticktext = df['artistName'].str.slice(0, 20) + '  ',
                                   fixedrange = True
                                   ),
                      margin = CHART_MARGIN
                      )

    return fig

# Function to generate top songs chart
def top_songs_chart(df, n, artist_label):
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
    fig.update_layout(title = 'Top {} Most Played Songs'.format(n),
                      xaxis_title = 'Total listening time (minutes)',
                      yaxis_title = '',
                      xaxis = dict(fixedrange = True),
                      yaxis = yaxis_format,
                      margin = CHART_MARGIN
                      )

    return fig

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

# Variable for author name
author_name = 'Gillano Lambengco'

# Variable for link to GitHub repo
github_link = 'https://github.com/glambengco/Spotify-Dash/tree/main'

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

about_me_style = {'display': 'flex',
                 'flex-direction': 'column',
                 'align-items': 'center',
                  'margin': 'auto', 
                  'width': '90%',
                  'max-width': '1200px',
                  'margin-top': '20px',
                  'margin-bottom': '20px',
                  }

# Dropdown menu Div style
dropdown_div_style = {'width': '90%', 
                      'max-width': '1200px',
                      'margin': 'auto',
                      'margin-top': '20px',
                      'margin-bottom': '20px',
                      'font-size': 20
                      }

# Dropdown style
dropdown_style = {'background': 'transparent'}

# Output style
output_style = {'margin': 'auto', 'max-width': '100%'}

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
                       html.Div([html.Label('by {}'.format(author_name)),
                                 html.A('Link to GitHub repo', href = github_link)
                                 ],
                                 style = about_me_style
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
    def format_output(fig):
        return html.Div(dcc.Graph(figure = fig), style = graph_style)
    
    n = 5

    if input_month == 'all':
        
        chart_1 = format_output(top_artists_chart(streaming_history, n))
        chart_2 = format_output(top_songs_chart(streaming_history, n, artist_label=True))
        chart_3 = format_output(time_by_month(streaming_history))
        chart_4 = format_output(time_by_day_of_week(streaming_history))
        chart_5 = format_output(time_by_weekday_weekend(streaming_history))
        chart_6 = format_output(time_by_hour(streaming_history))

        return html.Div(className='chart-item', 
                        children=[chart_1, chart_2, chart_3, chart_4, chart_5, chart_6],
                        style=chart_display
                       )
    
    elif input_month != 'Select month': 
        i = str(input_month)
        year = int(i.split()[0])
        month = int(i.split()[1])

        df_month = filter_by_month(streaming_history, year, month)

        chart_1 = format_output(top_artists_chart(df_month, n))
        chart_2 = format_output(top_songs_chart(df_month, n, artist_label=True))
        chart_3 = format_output(time_by_day_of_week(df_month))
        chart_4 = format_output(time_by_weekday_weekend(df_month))
        chart_5 = format_output(time_by_hour(df_month))

        return html.Div(className='chart-item', 
                        children=[chart_1, chart_2, chart_3, chart_4, chart_5],
                        style=chart_display
                       )
    
    else:
        return None

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)
