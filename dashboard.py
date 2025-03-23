import pandas as pd
import numpy as np
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import datetime

#read csv
df = pd.read_csv('/home/bart/Project_ADV_Python_git_linux/data_output.csv')
df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d %H:%M:%S')
df.columns = df.columns.str.strip() #to avoid space 

#volatilities, return 
df['Volatility'] = df['ClosePrice'].pct_change().rolling(window=2).std() * np.sqrt(2)
df['Return'] = (df['ClosePrice'] - df['OpenPrice']) / df['OpenPrice']
# daily_volatility, daily_return
daily_volatility = df['Volatility'].iloc[-1] if not pd.isnull(df['Volatility'].iloc[-1]) else 0
daily_return = df['Return'].iloc[-1] if not pd.isnull(df['Return'].iloc[-1]) else 0
open_price = df['OpenPrice'].iloc[-1]
close_price = df['ClosePrice'].iloc[-1]

def generate_daily_report():
    return f"""
    <h3>Daily Financial Report</h3>
    <p><strong>Open Price (Last):</strong> {open_price}</p>
    <p><strong>Close Price (Last):</strong> {close_price}</p>
    <p><strong>Volatility (Last Day):</strong> {daily_volatility:.2f}</p>
    <p><strong>Daily Return (Last Day):</strong> {daily_return*100:.2f}%</p>
    <p><strong>Date of Report:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    """

#to save the previous day's report as a file
def save_previous_report(report):
    previous_report_filename = '/home/bart/Project_ADV_Python_git_linux/previous_report.html'
    with open(previous_report_filename, 'w') as file:
        file.write(report)

def read_previous_report():
    previous_report_filename = '/home/bart/Project_ADV_Python_git_linux/previous_report.html'
    if os.path.exists(previous_report_filename):
        with open(previous_report_filename, 'r') as file:
            return file.read()
    else:
        return "No report available for the previous day."

#Dash application
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1('Stock Price Dashboard', style={'textAlign': 'center'}),
    dcc.Graph(
        id='time-series-graph',
        figure=px.line(df, x='Date', y='ClosePrice', title='ClosePrice Time Series')
    ),
    html.Div(id='daily-report', children=generate_daily_report()),  # Affichage du rapport quotidien
])

#updates daily report at 8 p.m.
@app.callback(
    Output('daily-report', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_daily_report(n):
    current_time = datetime.datetime.now().time()
    # Si c'est 20h, mettre à jour le rapport
    if current_time.hour == 20 and current_time.minute == 0:
        return generate_daily_report()
    else:
        return 'Daily report will be available at 8pm.'
        
#checks the time to update the daily report at 8 p.m.
app.layout.children.append(dcc.Interval(
    id='interval-component',
    interval=60000,  # Vérifier toutes les minutes
    n_intervals=0
))

if __name__ == '__main__':
    app.run(debug=True)
