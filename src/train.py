import pandas as pd
import numpy as np
from sklearn.linear_model import PoissonRegressor
from sklearn.preprocessing import StandardScaler
import streamlit as st

FEATURES = [
    'elo_diff', 'home_form_gd', 'away_form_gd',
    'home_form_wins', 'away_form_wins',
    'home_form_gf', 'away_form_gf',
    'home_form_ga', 'away_form_ga'
]

@st.cache_resource
def train_models():
    """Train Poisson models from features.csv directly."""
    features_df = pd.read_csv('features.csv')
    features_df['Year'] = pd.to_datetime(
        features_df['Date']).dt.year

    test_years = [2018, 2022]
    train_mask = ~features_df['Year'].isin(test_years)

    X = features_df[FEATURES].fillna(0)
    y_home = features_df['home_score']
    y_away = features_df['away_score']

    X_train = X[train_mask]
    y_home_train = y_home[train_mask]
    y_away_train = y_away[train_mask]

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    model_home = PoissonRegressor(alpha=0.1, max_iter=1000)
    model_away = PoissonRegressor(alpha=0.1, max_iter=1000)

    model_home.fit(X_train_scaled, y_home_train)
    model_away.fit(X_train_scaled, y_away_train)

    return model_home, model_away, scaler
