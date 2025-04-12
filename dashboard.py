import pandas as pd
import numpy as np
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from pathlib import Path
import base64

# Définition des chemins
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / 'data_history.csv'
REALTIME_DATA_FILE = BASE_DIR / 'data_output.csv'
LOGO_PATH = BASE_DIR / 'ESILV.png'



# Encodage du logo en base64
def encode_image(image_path):
    with open(image_path, 'rb') as f:
        encoded = base64.b64encode(f.read()).decode('ascii')
    return f'data:image/png;base64,{encoded}'

# Configuration des couleurs
COLORS = {
    'background': '#f8f9fa',
    'card_background': '#ffffff',
    'text': '#2c3e50',
    'text_secondary': '#6c757d',
    'increase': '#26a69a',
    'decrease': '#ef5350',
    'volatility': '#2196f3',
    'border': '#e0e0e0',
    'header_bg': '#ffffff',
    'shadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
    'hover_shadow': '0 6px 12px rgba(0, 0, 0, 0.15)',
    'gradient_start': '#2c3e50',
    'gradient_end': '#3498db',
    'accent': '#3498db',
    'success': '#2ecc71',
    'warning': '#f1c40f',
    'danger': '#e74c3c'
}

def calculate_sharpe_ratio(returns, risk_free_rate=0.03):
    """
    Calcule le ratio de Sharpe journalier
    :param returns: Série de rendements logarithmiques
    :param risk_free_rate: Taux sans risque annuel (3% par défaut)
    :return: Ratio de Sharpe journalier
    """
    if len(returns) < 2:
        return 0
        
    # Convertir le taux sans risque annuel en taux journalier
    daily_rf = np.log(1 + risk_free_rate) / 252
    
    # Calculer les rendements excédentaires
    excess_returns = returns - daily_rf
    
    # Calculer le ratio de Sharpe journalier (sans annualisation)
    vol = excess_returns.std()
    if vol == 0:
        return 0
        
    # Ratio de Sharpe journalier (pas d'annualisation avec sqrt(252))
    sharpe = excess_returns.mean() / vol
    return sharpe

def calculate_volatility(returns, period):
    """Calcule la volatilité selon la période choisie"""
    if period == 'day':
        # Volatilité journalière annualisée (252 jours de trading)
        window = min(20, len(returns))
        annualization = np.sqrt(252)
    elif period == 'week':
        # Volatilité hebdomadaire annualisée (52 semaines)
        window = min(8, len(returns))
        annualization = np.sqrt(52)
    else:  # month
        # Volatilité mensuelle annualisée (12 mois)
        window = min(6, len(returns))
        annualization = np.sqrt(12)
    
    volatility = returns.rolling(window=window, min_periods=1).std() * annualization * 100
    return volatility

def calculate_sortino_ratio(returns, risk_free_rate=0.03):
    """
    Calcule le ratio de Sortino journalier
    :param returns: Série de rendements logarithmiques
    :param risk_free_rate: Taux sans risque annuel (3% par défaut)
    :return: Ratio de Sortino journalier
    """
    if len(returns) < 2:
        return 0
        
    # Convertir le taux sans risque annuel en taux journalier
    daily_rf = np.log(1 + risk_free_rate) / 252
    
    # Calculer les rendements excédentaires
    excess_returns = returns - daily_rf
    
    # Calculer la volatilité négative (downside deviation)
    negative_returns = excess_returns[excess_returns < 0]
    if len(negative_returns) == 0:
        return 0
    downside_vol = negative_returns.std()
    if downside_vol == 0:
        return 0
        
    # Ratio de Sortino journalier
    sortino = excess_returns.mean() / downside_vol
    return sortino

def calculate_drawdown(returns):
    """
    Calcule le drawdown et le max drawdown
    :param returns: Série de rendements logarithmiques
    :return: drawdown, max_drawdown
    """
    if len(returns) < 2:
        return pd.Series(), 0
        
    # Calcul du rendement cumulé
    cum_returns = returns.cumsum()
    
    # Calcul du maximum cumulé
    cum_max = cum_returns.cummax()
    
    # Calcul du drawdown
    drawdown = cum_returns - cum_max
    
    # Max drawdown
    max_drawdown = drawdown.min()
    
    return drawdown, max_drawdown

def load_realtime_data():
    """Charge les données en temps réel"""
    try:
        if not os.path.exists(REALTIME_DATA_FILE):
            return pd.DataFrame()
            
        df = pd.read_csv(REALTIME_DATA_FILE, skipinitialspace=True, skiprows=1)
        df.columns = ['Date', 'OpenPrice', 'ClosePrice', 'High', 'Low']
        
        numeric_columns = ['OpenPrice', 'High', 'Low', 'ClosePrice']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        
        df['Return'] = df['ClosePrice'].pct_change().fillna(0)
        df['Volatility'] = df['ClosePrice'].pct_change().fillna(0).rolling(
            window=min(20, len(df)),
            min_periods=1
        ).std() * np.sqrt(252) * 100
        df['SharpeRatio'] = df['Return'].rolling(window=min(252, len(df))).apply(calculate_sharpe_ratio)
        
        return df
        
    except Exception:
        return pd.DataFrame()

def resample_data(df, period):
    """Rééchantillonne les données selon la période choisie"""
    if period == 'realtime':
        return df  # On retourne directement les données sans rééchantillonnage
    elif period == 'day':
        resampled = df.copy()
    elif period == 'week':
        resampled = df.resample('W', on='Date').agg({
            'OpenPrice': 'first',
            'High': 'max',
            'Low': 'min',
            'ClosePrice': 'last'
        }).reset_index()
    elif period == 'month':
        resampled = df.resample('M', on='Date').agg({
            'OpenPrice': 'first',
            'High': 'max',
            'Low': 'min',
            'ClosePrice': 'last'
        }).reset_index()
    else:
        return df

    # Calcul des rendements
    resampled['Return'] = resampled['ClosePrice'].pct_change().fillna(0)
    
    # Calcul de la volatilité adaptée à la période
    if period == 'day':
        window = min(20, len(resampled))
        annualization = np.sqrt(252)
    elif period == 'week':
        window = min(8, len(resampled))
        annualization = np.sqrt(52)
    else:  # month
        window = min(6, len(resampled))
        annualization = np.sqrt(12)
    
    resampled['Volatility'] = resampled['ClosePrice'].pct_change().fillna(0).rolling(
        window=window,
        min_periods=1
    ).std() * annualization * 100
    
    # Calcul du ratio de Sharpe
    resampled['SharpeRatio'] = resampled['Return'].rolling(
        window=min(252 if period == 'day' else 52 if period == 'week' else 12, len(resampled))
    ).apply(calculate_sharpe_ratio)
    
    return resampled.sort_values('Date')

def load_and_process_data():
    try:
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date'])
        return df.sort_values('Date')
    except Exception as e:
        print(f"Erreur lors du chargement des données: {str(e)}")
        return pd.DataFrame()

def create_daily_report(df):
    """Crée le rapport journalier basé uniquement sur data_output.csv"""
    try:
        if not os.path.exists(REALTIME_DATA_FILE):
            return html.Div("Données en temps réel non disponibles")
            
        try:
            realtime_df = pd.read_csv(REALTIME_DATA_FILE, skipinitialspace=True, skiprows=1)
            realtime_df.columns = ['Date', 'OpenPrice', 'ClosePrice', 'High', 'Low']
            realtime_df['Date'] = pd.to_datetime(realtime_df['Date'])
            
            if realtime_df.empty:
                return html.Div("Aucune donnée disponible")
                
            for col in ['OpenPrice', 'ClosePrice', 'High', 'Low']:
                realtime_df[col] = pd.to_numeric(realtime_df[col], errors='coerce')
            
            opening_price = realtime_df['OpenPrice'].iloc[0]
            highest_price = realtime_df['High'].max()
            lowest_price = realtime_df['Low'].min()
            
            closing_time = realtime_df[realtime_df['Date'].dt.strftime('%H:%M') == '17:30']
            closing_price = closing_time['ClosePrice'].iloc[-1] if not closing_time.empty else "-----"
            
            realtime_df['log_return'] = np.log(realtime_df['ClosePrice'] / realtime_df['ClosePrice'].shift(1))
            realtime_df['cum_return'] = realtime_df['log_return'].cumsum()
            
            drawdown, max_drawdown = calculate_drawdown(realtime_df['log_return'])
            realtime_df['drawdown'] = drawdown
            
            total_variation = realtime_df['log_return'].sum() * 100
            price_change = realtime_df['ClosePrice'].iloc[-1] - realtime_df['OpenPrice'].iloc[0]
            total_return = realtime_df['cum_return'].iloc[-1] * 100
            
            first_time = realtime_df['Date'].iloc[0]
            last_time = realtime_df['Date'].iloc[-1]
            minutes_elapsed = (last_time - first_time).total_seconds() / 60
            trading_minutes = min(390, minutes_elapsed)
            
            metrics_message = "Les informations seront disponibles à 20h"
            volatility_value = "-----"
            sharpe_value = "-----"
            sortino_value = "-----"
            return_value = "-----"
            max_dd_value = "-----"
            
            now = datetime.now()
            current_weekday = now.weekday()
            current_hour = now.hour
            
            if current_weekday >= 5:
                try:
                    volatility = realtime_df['log_return'].std() * np.sqrt(trading_minutes)
                    sharpe = calculate_sharpe_ratio(realtime_df['log_return'])
                    sortino = calculate_sortino_ratio(realtime_df['log_return'])
                    
                    metrics_message = "Métriques du vendredi"
                    volatility_value = f"{volatility*100:.2f}%"
                    sharpe_value = f"{sharpe:.2f}"
                    sortino_value = f"{sortino:.2f}"
                    return_value = f"{total_return:.2f}%"
                    max_dd_value = f"{max_drawdown*100:.2f}%"
                except Exception:
                    pass
                    
            elif current_hour >= 20:
                try:
                    volatility = realtime_df['log_return'].std() * np.sqrt(trading_minutes)
                    sharpe = calculate_sharpe_ratio(realtime_df['log_return'])
                    sortino = calculate_sortino_ratio(realtime_df['log_return'])
                    
                    metrics_message = "Métriques de la journée"
                    volatility_value = f"{volatility*100:.2f}%"
                    sharpe_value = f"{sharpe:.2f}"
                    sortino_value = f"{sortino:.2f}"
                    return_value = f"{total_return:.2f}%"
                    max_dd_value = f"{max_drawdown*100:.2f}%"
                except Exception:
                    pass
            
            return html.Div([
                html.Div([
                    html.H3('Analyses journalières', style={
                        'color': COLORS['text'],
                        'marginBottom': '20px',
                        'textAlign': 'center',
                        'fontSize': '1.8em',
                        'fontWeight': 'bold',
                        'textShadow': '1px 1px 2px rgba(0,0,0,0.1)'
                    })
                ], style={
                    'backgroundColor': COLORS['header_bg'],
                    'padding': '20px',
                    'borderRadius': '10px',
                    'boxShadow': COLORS['shadow'],
                    'marginBottom': '20px'
                }),
                html.Div([
                    html.Div([
                        html.H4('Prix', style={
                            'color': COLORS['text'],
                            'marginBottom': '15px',
                            'fontSize': '1.3em',
                            'borderBottom': f'2px solid {COLORS["border"]}',
                            'paddingBottom': '10px'
                        }),
                        html.Div([
                            html.P(f"Ouverture: {opening_price:.2f} €", style={'margin': '10px 0'}),
                            html.P(f"Clôture: {closing_price if isinstance(closing_price, str) else f'{closing_price:.2f} €'}", 
                                  style={'margin': '10px 0'}),
                            html.P(f"Plus haut: {highest_price:.2f} €", style={'margin': '10px 0'}),
                            html.P(f"Plus bas: {lowest_price:.2f} €", style={'margin': '10px 0'}),
                            html.P(
                                f"Variation: {price_change:.2f} € ({total_variation:.2f}%)", 
                                style={'margin': '10px 0'}
                            )
                        ])
                    ], style={
                        'backgroundColor': COLORS['card_background'],
                        'padding': '25px',
                        'borderRadius': '10px',
                        'boxShadow': COLORS['shadow'],
                        'border': f"1px solid {COLORS['border']}",
                        'marginRight': '20px',
                        'flex': '1'
                    }),
                    html.Div([
                        html.H4('Métriques', style={
                            'color': COLORS['text'],
                            'marginBottom': '15px',
                            'fontSize': '1.3em',
                            'borderBottom': f'2px solid {COLORS["border"]}',
                            'paddingBottom': '10px'
                        }),
                        html.Div([
                            html.P(metrics_message, style={
                                'color': COLORS['text_secondary'],
                                'fontStyle': 'italic',
                                'marginBottom': '15px'
                            }),
                            html.P(f"Volatilité: {volatility_value}", style={'margin': '10px 0'}),
                            html.P(f"Ratio de Sharpe: {sharpe_value}", style={'margin': '10px 0'}),
                            html.P(f"Ratio de Sortino: {sortino_value}", style={'margin': '10px 0'}),
                            html.P(f"Rendement cumulé: {return_value}", style={'margin': '10px 0'}),
                            html.P(f"Max Drawdown: {max_dd_value}", style={'margin': '10px 0'})
                        ])
                    ], style={
                        'backgroundColor': COLORS['card_background'],
                        'padding': '25px',
                        'borderRadius': '10px',
                        'boxShadow': COLORS['shadow'],
                        'border': f"1px solid {COLORS['border']}",
                        'flex': '1'
                    })
                ], style={
                    'display': 'flex',
                    'justifyContent': 'center',
                    'marginBottom': '30px',
                    'gap': '20px'
                })
            ])
            
        except Exception:
            return html.Div("Erreur lors du traitement des données")
            
    except Exception:
        return html.Div("Erreur lors de la création du rapport journalier")

def update_history_data():
    """Met à jour data_history.csv avec les données finales de la journée à 20h"""
    try:
        now = datetime.now()
        current_hour = now.hour
        
        # Vérifier si c'est 20h
        if current_hour == 20:
            # Lire les données en temps réel
            realtime_df = pd.read_csv(REALTIME_DATA_FILE, skipinitialspace=True, skiprows=1)
            realtime_df.columns = ['Date', 'OpenPrice', 'ClosePrice', 'High', 'Low']
            realtime_df['Date'] = pd.to_datetime(realtime_df['Date'])
            
            # Obtenir la date d'aujourd'hui
            today = now.date()
            
            # Vérifier si les données d'aujourd'hui sont déjà dans l'historique
            history_df = pd.read_csv(DATA_FILE)
            history_df['Date'] = pd.to_datetime(history_df['Date'])
            
            # Filtrer pour avoir uniquement les données d'aujourd'hui
            today_data = realtime_df[realtime_df['Date'].dt.date == today]
            
            if not today_data.empty:
                # Vérifier si la date existe déjà dans l'historique
                if not (history_df['Date'].dt.date == today).any():
                    # Ajouter les données d'aujourd'hui à l'historique
                    new_data = pd.DataFrame({
                        'Date': [today_data['Date'].iloc[-1]],
                        'OpenPrice': [today_data['OpenPrice'].iloc[0]],
                        'ClosePrice': [today_data['ClosePrice'].iloc[-1]],
                        'High': [today_data['High'].max()],
                        'Low': [today_data['Low'].min()]
                    })
                    
                    # Concaténer et sauvegarder
                    updated_history = pd.concat([history_df, new_data], ignore_index=True)
                    updated_history.to_csv(DATA_FILE, index=False)
                    
    except Exception:
        pass

app = dash.Dash(__name__)

app.layout = html.Div([
    # En-tête avec logo et titre
    html.Div([
        html.Div([
            html.Img(
                src=encode_image(LOGO_PATH),
                style={
                    'height': '80px',
                    'position': 'absolute',
                    'left': '20px',
                    'filter': 'drop-shadow(2px 2px 4px rgba(0,0,0,0.1))',
                    'transition': 'transform 0.3s ease'
                }
            ),
            html.H1('Analyse Technique du CAC 40', 
                    style={
                        'textAlign': 'center',
                        'marginBottom': '30px',
                        'fontSize': '2.8em',
                        'fontWeight': 'bold',
                        'color': COLORS['text'],
                        'textShadow': '2px 2px 4px rgba(0,0,0,0.1)',
                        'background': f'linear-gradient(45deg, {COLORS["gradient_start"]}, {COLORS["gradient_end"]})',
                        'WebkitBackgroundClip': 'text',
                        'WebkitTextFillColor': 'transparent',
                        'padding': '20px 0'
                    })
        ], style={
            'position': 'relative',
            'width': '100%',
            'marginBottom': '30px',
            'padding': '20px 0',
            'backgroundColor': COLORS['header_bg'],
            'borderRadius': '15px',
            'boxShadow': COLORS['shadow'],
            'transition': 'all 0.3s ease'
        })
    ]),
    
    # Rapport journalier
    html.Div(id='daily-report'),
    
    # Filtres temporels avec style amélioré
    html.Div([
        html.Div([
            dcc.DatePickerRange(
                id='date-range',
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now(),
                style={
                    'marginRight': '20px',
                    'borderRadius': '8px',
                    'border': f"1px solid {COLORS['border']}",
                    'padding': '12px',
                    'backgroundColor': COLORS['card_background'],
                    'boxShadow': COLORS['shadow']
                }
            ),
            dcc.RadioItems(
                id='period-selector',
                options=[
                    {'label': 'Temps réel', 'value': 'realtime'},
                    {'label': 'Journalier', 'value': 'day'},
                    {'label': 'Hebdomadaire', 'value': 'week'},
                    {'label': 'Mensuel', 'value': 'month'}
                ],
                value='day',
                labelStyle={
                    'display': 'inline-block',
                    'marginRight': '20px',
                    'padding': '10px 20px',
                    'borderRadius': '8px',
                    'backgroundColor': COLORS['card_background'],
                    'boxShadow': COLORS['shadow'],
                    'cursor': 'pointer',
                    'transition': 'all 0.3s ease',
                    'border': f"1px solid {COLORS['border']}"
                },
                style={'display': 'inline-block'}
            )
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'marginBottom': '20px',
            'padding': '20px',
            'backgroundColor': COLORS['card_background'],
            'borderRadius': '15px',
            'boxShadow': COLORS['shadow'],
            'border': f"1px solid {COLORS['border']}"
        })
    ]),
    
    # Graphiques avec style amélioré
    html.Div([
        html.Div([
            dcc.Graph(id='candlestick-graph')
        ], style={
            'backgroundColor': COLORS['card_background'],
            'padding': '25px',
            'borderRadius': '15px',
            'boxShadow': COLORS['shadow'],
            'marginBottom': '30px',
            'border': f"1px solid {COLORS['border']}",
            'transition': 'all 0.3s ease'
        }),
        html.Div([
            dcc.Graph(id='volatility-graph')
        ], style={
            'backgroundColor': COLORS['card_background'],
            'padding': '25px',
            'borderRadius': '15px',
            'boxShadow': COLORS['shadow'],
            'marginBottom': '30px',
            'border': f"1px solid {COLORS['border']}",
            'transition': 'all 0.3s ease'
        })
    ]),
    
    # Pied de page avec style amélioré
    html.Div([
        html.Hr(style={
            'border': 'none',
            'height': '1px',
            'backgroundColor': COLORS['border'],
            'margin': '30px 0'
        }),
        html.Div([
            html.P('Projet réalisé par Barthélémy BENGLOAN et Gilles Delpy SOP - IF1 ESILV', 
                   style={
                       'color': COLORS['text_secondary'],
                       'fontSize': '0.9em',
                       'textAlign': 'center',
                       'fontStyle': 'italic',
                       'marginBottom': '10px'
                   })
        ], style={
            'padding': '20px',
            'backgroundColor': COLORS['card_background'],
            'borderRadius': '15px',
            'boxShadow': COLORS['shadow']
        })
    ]),
    
    # Intervalle de mise à jour
    dcc.Interval(
        id='interval-component',
        interval=300000,  # 5 minutes
        n_intervals=0
    )
], style={
    'backgroundColor': COLORS['background'],
    'minHeight': '100vh',
    'padding': '30px',
    'fontFamily': 'Arial, sans-serif',
    'maxWidth': '1400px',
    'margin': '0 auto'
})

@app.callback(
    [Output('candlestick-graph', 'figure'),
     Output('volatility-graph', 'figure'),
     Output('daily-report', 'children')],
    [Input('interval-component', 'n_intervals'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('period-selector', 'value')]
)
def update_graphs(n, start_date, end_date, period):
    # Mettre à jour l'historique à 20h
    update_history_data()
    
    if period == 'realtime':
        df = load_realtime_data()
        if df.empty:
            empty_fig = go.Figure()
            empty_fig.update_layout(
                title={
                    'text': "Aucune donnée en temps réel disponible",
                    'font': {'size': 24, 'color': COLORS['text']},
                    'x': 0.5,
                    'y': 0.5
                }
            )
            return empty_fig, empty_fig, html.Div("Aucune donnée en temps réel disponible")
    else:
        df = load_and_process_data()
        if df.empty:
            empty_fig = go.Figure()
            empty_fig.update_layout(
                title={
                    'text': "Aucune donnée disponible",
                    'font': {'size': 24, 'color': COLORS['text']},
                    'x': 0.5,
                    'y': 0.5
                }
            )
            return empty_fig, empty_fig, html.Div("Aucune donnée disponible")
        
        # Conversion des dates en datetime
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        
        # Filtrage des données selon la période sélectionnée
        mask = (df['Date'] >= start_date) & (df['Date'] <= end_date)
        df = df.loc[mask]
    
    # Application du traitement des données
    df = resample_data(df, period)
    
    if len(df) == 0:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            title={
                'text': "Aucune donnée pour la période sélectionnée",
                'font': {'size': 24, 'color': COLORS['text']},
                'x': 0.5,
                'y': 0.5
            }
        )
        return empty_fig, empty_fig, html.Div("Aucune donnée pour la période sélectionnée")
    
    # Création du rapport journalier
    daily_report = create_daily_report(df)
    
    # Graphique chandelier
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
        ]
    )
    
    title_text = 'Évolution du CAC40 en Temps Réel' if period == 'realtime' else 'Évolution du CAC40'
    
    candlestick.update_layout(
        title={
            'text': title_text,
            'font': {'size': 24, 'color': COLORS['text']},
            'x': 0.5,
            'y': 0.95
        },
        yaxis_title='Prix (€)',
        template='plotly_white',
        height=600,
        margin={'l': 50, 'r': 50, 't': 80, 'b': 50},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_rangeslider_visible=False,
        showlegend=False,
        hovermode='x unified',
        font={'family': 'Arial, sans-serif'},
        xaxis=dict(
            gridcolor=COLORS['border'],
            showgrid=True
        ),
        yaxis=dict(
            gridcolor=COLORS['border'],
            showgrid=True
        )
    )
    
    # Graphique de volatilité
    volatility = px.line(
        df, 
        x='Date', 
        y='Volatility',
        title='Volatilité' + (' en Temps Réel' if period == 'realtime' else ''),
        labels={'Volatility': 'Volatilité (%)', 'Date': 'Date'},
        template='plotly_white',
        height=300,
        color_discrete_sequence=[COLORS['volatility']]
    ).update_layout(
        title={
            'text': 'Volatilité' + (' en Temps Réel' if period == 'realtime' else ''),
            'font': {'size': 24, 'color': COLORS['text']},
            'x': 0.5,
            'y': 0.95
        },
        margin={'l': 50, 'r': 50, 't': 80, 'b': 50},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        hovermode='x unified',
        font={'family': 'Arial, sans-serif'},
        xaxis=dict(
            gridcolor=COLORS['border'],
            showgrid=True
        ),
        yaxis=dict(
            gridcolor=COLORS['border'],
            showgrid=True
        )
    )
    
    return candlestick, volatility, daily_report
print(f"Chemin vers le fichier des données historiques : {DATA_FILE}")
print(f"Chemin vers le fichier des données en temps réel : {REALTIME_DATA_FILE}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8051)


