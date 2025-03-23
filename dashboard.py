import pandas as pd
import numpy as np
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import datetime

# Lire le fichier CSV mis à jour
df = pd.read_csv('/home/bart/Project_ADV_Python_git_linux/data_output.csv')

# Convertir la colonne Date en format datetime
df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d %H:%M:%S')
df.columns = df.columns.str.strip()
# Vérification des colonnes présentes
print(df.columns)

# Calcul de la volatilité quotidienne (écart type des prix de clôture)
df['Volatility'] = df['ClosePrice'].pct_change().rolling(window=2).std() * np.sqrt(2)

# Calcul du rendement (pour la journée)
df['Return'] = (df['ClosePrice'] - df['OpenPrice']) / df['OpenPrice']

# Vérifier les premières lignes après calcul
print(df.head())

# Sélectionner les prix d'ouverture et de clôture pour la journée
open_price = df['OpenPrice'].iloc[-1]
close_price = df['ClosePrice'].iloc[-1]

# Calculer la volatilité du jour
volatility = df['Volatility'].iloc[-1] if not pd.isnull(df['Volatility'].iloc[-1]) else 0

# Calculer le rendement du jour
daily_return = df['Return'].iloc[-1] if not pd.isnull(df['Return'].iloc[-1]) else 0

# Créer une fonction qui génère le rapport quotidien
def generate_daily_report():
    return f"""
    <h3>Daily Financial Report</h3>
    <p><strong>Open Price (Last):</strong> {open_price}</p>
    <p><strong>Close Price (Last):</strong> {close_price}</p>
    <p><strong>Volatility (Last Day):</strong> {volatility:.2f}</p>
    <p><strong>Daily Return (Last Day):</strong> {daily_return*100:.2f}%</p>
    <p><strong>Date of Report:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    """

# Fonction pour sauvegarder le rapport du jour précédent dans un fichier
def save_previous_report(report):
    previous_report_filename = '/home/bart/Project_ADV_Python_git_linux/previous_report.html'
    with open(previous_report_filename, 'w') as file:
        file.write(report)

# Lire le rapport précédent sauvegardé, s'il existe
def read_previous_report():
    previous_report_filename = '/home/bart/Project_ADV_Python_git_linux/previous_report.html'
    if os.path.exists(previous_report_filename):
        with open(previous_report_filename, 'r') as file:
            return file.read()
    else:
        return "No report available for the previous day."


# Créer l'application Dash
app = dash.Dash(__name__)

# Layout de l'application
app.layout = html.Div([
    html.H1('Stock Price Dashboard', style={'textAlign': 'center'}),
    dcc.Graph(
        id='time-series-graph',
        figure=px.line(df, x='Date', y='ClosePrice', title='ClosePrice Time Series')
    ),
    html.Div(id='daily-report', children=generate_daily_report()),  # Affichage du rapport quotidien
])

# Fonction qui met à jour le rapport quotidien tous les jours à 20h
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

# Ajout d'un composant qui vérifie le temps pour mettre à jour le rapport quotidien à 20h
app.layout.children.append(dcc.Interval(
    id='interval-component',
    interval=60000,  # Vérifier toutes les minutes
    n_intervals=0
))

# Démarrer le serveur Dash
if __name__ == '__main__':
    app.run(debug=True)
