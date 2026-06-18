import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.groups import GROUPS, ALL_TEAMS, get_flag
from src.model import predict_match, get_live_form, FEATURES
from src.simulator import run_simulation
from src.data import (load_results, save_result, delete_result,
                      get_group_standings)
from src.train import train_models

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="WC 2026 Predictor",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Train models ──────────────────────────────────────────────
with st.spinner("Loading models..."):
    model_home, model_away, scaler = train_models()

# ── Load team strength ────────────────────────────────────────
@st.cache_data
def load_team_strength():
    return pd.read_csv('team_strength_2026.csv')

team_strength_df = load_team_strength()

# ── Load live results ─────────────────────────────────────────
if 'results' not in st.session_state:
    st.session_state.results = load_results()

live_results = st.session_state.results

# ── Sidebar navigation ────────────────────────────────────────
st.sidebar.title("🏆 WC 2026 Predictor")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["🏆 Predictions", "📊 Group Standings",
     "🔮 Match Predictor", "⚽ Enter Scores"]
)

st.sidebar.markdown("---")
st.sidebar.metric("Matches played", len(live_results))
st.sidebar.markdown("*Predictions update with every result*")

# ══════════════════════════════════════════════════════════════
# PAGE 1 — PREDICTIONS
# ══════════════════════════════════════════════════════════════
if page == "🏆 Predictions":
    st.title("🏆 FIFA World Cup 2026 — Tournament Predictions")
    st.markdown(f"*Based on {len(live_results)} real match results*")

    with st.spinner("Running 5,000 simulations..."):
        sim_results = run_simulation(
            team_strength_df, model_home, model_away,
            scaler, live_results, n_sims=5000
        )

    top10 = sim_results.head(10).copy()
    top10['label'] = top10['team'].apply(
        lambda t: f"{get_flag(t)} {t}"
    )

    fig = px.bar(
        top10,
        x='win_%', y='label',
        orientation='h',
        title='Tournament Win Probability — Top 10',
        labels={'win_%': 'Win Probability (%)', 'label': ''},
        color='win_%',
        color_continuous_scale='Greens',
        text='win_%'
    )
    fig.update_traces(texttemplate='%{text}%', textposition='outside')
    fig.update_layout(
        height=450,
        showlegend=False,
        coloraxis_showscale=False,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white'
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Full Predictions Table")
    display_df = sim_results.copy()
    display_df['Team'] = display_df['team'].apply(
        lambda t: f"{get_flag(t)} {t}"
    )
    display_df = display_df.rename(columns={
        'win_%'    : 'Win %',
        'final_%'  : 'Final %',
        'semi_%'   : 'Semi %',
        'qualify_%': 'Qualify %'
    })[['Team', 'Win %', 'Final %', 'Semi %', 'Qualify %']]

    st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True,
        height=600
    )
