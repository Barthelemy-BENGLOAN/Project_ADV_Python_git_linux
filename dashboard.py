import pandas as pd
import numpy as np
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from pathlib import Path

# Définition des chemins
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / 'data_output.csv'
PREVIOUS_REPORT_FILE = BASE_DIR / 'previous_report.html'

def load_and_process_data():
    try:
        # Lecture des données avec gestion des erreurs
        df = pd.read_csv(DATA_FILE)
        
        # Conversion des colonnes en nombres
        numeric_columns = ['OpenPrice', 'ClosePrice', 'High', 'Low']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Conversion de la date
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Suppression des lignes avec des valeurs manquantes
        df = df.dropna()
        
        # Tri par date
        df = df.sort_values('Date')
        
        # Calcul de la volatilité avec gestion des erreurs
        if len(df) > 0:
            df['Volatility'] = df['ClosePrice'].pct_change().fillna(0).rolling(window=min(20, len(df))).std() * np.sqrt(252) * 100
        else:
            df['Volatility'] = 0
            
        return df
    except Exception as e:
        print(f"Erreur lors du chargement des données: {str(e)}")
        return pd.DataFrame()

# Métriques pour le rapport
def generate_daily_report(df):
    last_data = df.iloc[-1]
    daily_volatility = df['Volatility'].iloc[-1]
    daily_return = df['Return'].iloc[-1]
    daily_high = df['High'].max()
    daily_low = df['Low'].min()
    current_price = last_data['ClosePrice']
    open_price = df.iloc[0]['OpenPrice']
    price_change = current_price - open_price
    price_change_pct = (price_change / open_price) * 100
    return f"""
    <div style='background-color: #ffffff; padding: 20px; border-radius: 10px; margin: 20px 0; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);'>
        <h3 style='color: #2c3e50; margin-bottom: 20px;'>Rapport du CAC40</h3>
        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 20px;'>
            <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px;'>
                <h4 style='color: #2c3e50; margin-bottom: 15px;'>Prix</h4>
                <p style='margin: 10px 0;'><strong>Prix actuel:</strong> <span style='color: {("green" if price_change >= 0 else "red")};'>{current_price:.2f} €</span></p>
                <p style='margin: 10px 0;'><strong>Prix d'ouverture:</strong> {open_price:.2f} €</p>
                <p style='margin: 10px 0;'><strong>Plus haut:</strong> {daily_high:.2f} €</p>
                <p style='margin: 10px 0;'><strong>Plus bas:</strong> {daily_low:.2f} €</p>
            </div>
            <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px;'>
                <h4 style='color: #2c3e50; margin-bottom: 15px;'>Performance</h4>
                <p style='margin: 10px 0;'><strong>Variation:</strong> <span style='color: {("green" if price_change >= 0 else "red")};'>{price_change:.2f} € ({price_change_pct:.2f}%)</span></p>
                <p style='margin: 10px 0;'><strong>Volatilité:</strong> {daily_volatility:.2f}%</p>
                <p style='margin: 10px 0;'><strong>Dernier rendement:</strong> <span style='color: {("green" if daily_return >= 0 else "red")};'>{daily_return:.2f}%</span></p>
                <p style='margin: 10px 0;'><strong>Mise à jour:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>
    </div>
    """

def save_previous_report(report):
    with open(PREVIOUS_REPORT_FILE, 'w') as file:
        file.write(report)

def read_previous_report():
    if os.path.exists(PREVIOUS_REPORT_FILE):
        with open(PREVIOUS_REPORT_FILE, 'r') as file:
            return file.read()
    return "Aucun rapport disponible pour la veille."

# Application Dash avec thème personnalisé
app = dash.Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ]
)

# Chargement initial des données
df = load_and_process_data()

# Configuration des couleurs et du style
COLORS = {
    'background': '#f5f6fa',
    'card_background': '#ffffff',
    'text': '#2c3e50',
    'increase': '#26a69a',
    'decrease': '#ef5350',
    'volatility': '#2196f3'
}

app.layout = html.Div([
    # En-tête
    html.Div([
        html.H1('Tableau de Bord CAC40', 
                style={
                    'textAlign': 'center', 
                    'color': COLORS['text'],
                    'marginBottom': '30px',
                    'fontSize': '2.5em',
                    'fontWeight': 'bold',
                    'textShadow': '2px 2px 4px rgba(0,0,0,0.1)'
                }),
        
        # Informations de mise à jour
        html.Div([
            html.P(f"Dernière mise à jour: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                  id='last-update',
                  style={
                      'textAlign': 'center',
                      'color': COLORS['text'],
                      'fontSize': '1.1em',
                      'marginBottom': '20px'
                  })
        ])
    ]),
    
    # Container pour les graphiques
    html.Div([
        # Graphique en chandelier
        html.Div([
            dcc.Graph(
                id='candlestick-graph',
                figure=go.Figure(
                    data=[
                        go.Candlestick(
                            x=df['Date'],
                            open=df['OpenPrice'],
                            high=df['High'],
                            low=df['Low'],
                            close=df['ClosePrice'],
                            increasing_line_color=COLORS['increase'],
                            decreasing_line_color=COLORS['decrease'],
                            increasing_fillcolor=COLORS['increase'],
                            decreasing_fillcolor=COLORS['decrease']
                        )
                    ],
                    layout=go.Layout(
                        title={
                            'text': 'Évolution du CAC40',
                            'font': {'size': 24, 'color': COLORS['text']}
                        },
                        yaxis_title='Prix (€)',
                        template='plotly_white',
                        height=600,
                        margin={'l': 50, 'r': 50, 't': 80, 'b': 50},
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis_rangeslider_visible=False,
                        showlegend=False,
                        hovermode='x unified'
                    )
                ),
                config={
                    'displayModeBar': True,
                    'scrollZoom': True,
                    'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'eraseshape']
                }
            )
        ], style={'marginBottom': '20px'}),
        
        # Graphique de volatilité
        html.Div([
            dcc.Graph(
                id='volatility-graph',
                figure=px.line(
                    df, 
                    x='Date', 
                    y='Volatility',
                    title='Volatilité',
                    labels={'Volatility': 'Volatilité (%)', 'Date': 'Date'},
                    template='plotly_white',
                    height=300,
                    color_discrete_sequence=[COLORS['volatility']]
                ).update_layout(
                    title={
                        'text': 'Volatilité',
                        'font': {'size': 24, 'color': COLORS['text']}
                    },
                    margin={'l': 50, 'r': 50, 't': 80, 'b': 50},
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=False,
                    hovermode='x unified'
                ),
                config={
                    'displayModeBar': True,
                    'scrollZoom': True
                }
            )
        ])
    ], style={
        'backgroundColor': COLORS['card_background'],
        'padding': '20px',
        'borderRadius': '10px',
        'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'
    }),
    
    # Intervalle de mise à jour
    dcc.Interval(
        id='interval-component',
        interval=300000,  # mise à jour toutes les 5 minutes
        n_intervals=0
    )
], style={
    'backgroundColor': COLORS['background'],
    'minHeight': '100vh',
    'padding': '20px',
    'fontFamily': 'Arial, sans-serif'
})

@app.callback(
    [Output('candlestick-graph', 'figure'),
     Output('volatility-graph', 'figure'),
     Output('last-update', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_graphs(n):
    # Rechargement des données
    df = load_and_process_data()
    
    # Mise à jour du graphique chandelier
    candlestick = go.Figure(
        data=[
            go.Candlestick(
                x=df['Date'],
                open=df['OpenPrice'],
                high=df['High'],
                low=df['Low'],
                close=df['ClosePrice'],
                increasing_line_color=COLORS['increase'],
                decreasing_line_color=COLORS['decrease'],
                increasing_fillcolor=COLORS['increase'],
                decreasing_fillcolor=COLORS['decrease']
            )
        ],
        layout=go.Layout(
            title={
                'text': 'Évolution du CAC40',
                'font': {'size': 24, 'color': COLORS['text']}
            },
            yaxis_title='Prix (€)',
            template='plotly_white',
            height=600,
            margin={'l': 50, 'r': 50, 't': 80, 'b': 50},
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_rangeslider_visible=False,
            showlegend=False,
            hovermode='x unified'
        )
    )
    
    # Mise à jour du graphique de volatilité
    volatility = px.line(
        df, 
        x='Date', 
        y='Volatility',
        title='Volatilité',
        labels={'Volatility': 'Volatilité (%)', 'Date': 'Date'},
        template='plotly_white',
        height=300,
        color_discrete_sequence=[COLORS['volatility']]
    ).update_layout(
        title={
            'text': 'Volatilité',
            'font': {'size': 24, 'color': COLORS['text']}
        },
        margin={'l': 50, 'r': 50, 't': 80, 'b': 50},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        hovermode='x unified'
    )
    
    # Mise à jour de l'horodatage
    last_update = f"Dernière mise à jour: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    return candlestick, volatility, last_update

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
