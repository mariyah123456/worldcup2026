import streamlit as st
import pandas as pd
import numpy as np
import pickle
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import PoissonRegressor
from sklearn.preprocessing import StandardScaler

from src.groups import GROUPS, ALL_TEAMS, get_flag
from src.model import predict_match, get_live_form, FEATURES
from src.simulator import run_simulation
from src.data import (load_results, save_result, delete_result,
                      get_group_standings)

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="WC 2026 Predictor",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Load models ───────────────────────────────────────────────
@st.cache_resource
def load_models():
    with open('data/model_home.pkl', 'rb') as f:
        model_home = pickle.load(f)
    with open('data/model_away.pkl', 'rb') as f:
        model_away = pickle.load(f)
    with open('data/scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
    return model_home, model_away, scaler

@st.cache_data
def load_team_strength():
    return pd.read_csv('data/team_strength_2026.csv')

model_home, model_away, scaler = load_models()
team_strength_df = load_team_strength()

# ── Load live results ─────────────────────────────────────────
if 'results' not in st.session_state:
    st.session_state.results = load_results()

live_results = st.session_state.results

# ── Sidebar navigation ────────────────────────────────────────
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/en/thumb/5/5e/FIFA_World_Cup_2026_logo.png/250px-FIFA_World_Cup_2026_logo.png",
    width=200
)
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

    # Top 10 bar chart
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

    # Full table
    st.markdown("### Full Predictions Table")
    col1, col2 = st.columns([1, 2])

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

# ══════════════════════════════════════════════════════════════
# PAGE 2 — GROUP STANDINGS
# ══════════════════════════════════════════════════════════════
elif page == "📊 Group Standings":
    st.title("📊 Group Stage Standings")
    st.markdown(f"*{len(live_results)} matches played*")

    standings = get_group_standings(live_results, GROUPS)

    # Display 2 groups per row
    groups_list = list(standings.items())
    for i in range(0, len(groups_list), 2):
        col1, col2 = st.columns(2)

        for col, (group, df) in zip(
                [col1, col2], groups_list[i:i+2]):
            with col:
                st.markdown(f"### Group {group}")
                display = df.copy()
                display.index = display.index.map(
                    lambda t: f"{get_flag(t)} {t}"
                )
                display['GD'] = display['GD'].apply(
                    lambda x: f"+{int(x)}" if x > 0
                    else str(int(x))
                )
                display = display.rename(columns={
                    'Pts': 'Pts', 'W': 'W', 'D': 'D',
                    'L': 'L', 'GF': 'GF', 'GA': 'GA'
                })
                display = display[['Pts','W','D','L',
                                   'GF','GA','GD']]
                display = display.astype(
                    {'Pts': int, 'W': int, 'D': int,
                     'L': int, 'GF': int, 'GA': int}
                )
                st.dataframe(
                    display,
                    use_container_width=True
                )

# ══════════════════════════════════════════════════════════════
# PAGE 3 — MATCH PREDICTOR
# ══════════════════════════════════════════════════════════════
elif page == "🔮 Match Predictor":
    st.title("🔮 Match Predictor")
    st.markdown("Select any two teams to get a prediction.")

    col1, col2 = st.columns(2)
    with col1:
        home_team = st.selectbox(
            "🏠 Home Team", ALL_TEAMS, index=0)
    with col2:
        away_team = st.selectbox(
            "✈️ Away Team", ALL_TEAMS, index=1)

    if home_team == away_team:
        st.warning("Please select different teams!")
    else:
        if st.button("🔮 Predict", type="primary",
                     use_container_width=True):
            result = predict_match(
                home_team, away_team, team_strength_df,
                model_home, model_away, scaler, live_results
            )

            if result:
                st.markdown("---")

                # Main result
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric(
                        f"{get_flag(home_team)} {home_team}",
                        f"{result['prob_home_win']:.1%}",
                        "Win probability"
                    )
                with c2:
                    st.metric(
                        "Draw",
                        f"{result['prob_draw']:.1%}",
                        f"Predicted: {result['predicted_score'][0]}-{result['predicted_score'][1]}"
                    )
                with c3:
                    st.metric(
                        f"{get_flag(away_team)} {away_team}",
                        f"{result['prob_away_win']:.1%}",
                        "Win probability"
                    )

                st.markdown("---")

                # Expected goals
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### Expected Goals")
                    fig = go.Figure(go.Bar(
                        x=[home_team, away_team],
                        y=[result['lambda_home'],
                           result['lambda_away']],
                        marker_color=['#1a6b3c', '#c41e3a'],
                        text=[f"{result['lambda_home']:.2f}",
                              f"{result['lambda_away']:.2f}"],
                        textposition='outside'
                    ))
                    fig.update_layout(
                        height=300,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='white',
                        showlegend=False
                    )
                    st.plotly_chart(fig,
                                   use_container_width=True)

                with col2:
                    st.markdown("### Most Likely Scorelines")
                    for (i, j), prob in result['top5_scorelines']:
                        bar_width = int(prob * 200)
                        st.markdown(
                            f"**{i}-{j}** &nbsp;&nbsp; "
                            f"`{'█' * bar_width}` "
                            f"{prob:.1%}"
                        )

                # Form
                st.markdown("---")
                st.markdown("### Tournament Form")
                fc1, fc2 = st.columns(2)
                with fc1:
                    hf = result['home_form']
                    st.markdown(
                        f"**{get_flag(home_team)} {home_team}**  \n"
                        f"W{hf['form_wins']} "
                        f"D{hf['form_draws']} "
                        f"L{hf['form_losses']} | "
                        f"GD: {hf['form_gd']:+d}"
                    )
                with fc2:
                    af = result['away_form']
                    st.markdown(
                        f"**{get_flag(away_team)} {away_team}**  \n"
                        f"W{af['form_wins']} "
                        f"D{af['form_draws']} "
                        f"L{af['form_losses']} | "
                        f"GD: {af['form_gd']:+d}"
                    )

# ══════════════════════════════════════════════════════════════
# PAGE 4 — ENTER SCORES (password protected)
# ══════════════════════════════════════════════════════════════
elif page == "⚽ Enter Scores":
    st.title("⚽ Enter Match Results")

    # Password protection
    if 'admin_auth' not in st.session_state:
        st.session_state.admin_auth = False

    if not st.session_state.admin_auth:
        pwd = st.text_input("Enter admin password",
                            type="password")
        if st.button("Login"):
            if pwd == st.secrets.get("ADMIN_PASSWORD",
                                     "worldcup2026"):
                st.session_state.admin_auth = True
                st.rerun()
            else:
                st.error("Incorrect password")
    else:
        st.success("✓ Logged in as admin")

        # Score entry
        st.markdown("### Add / Update Result")
        c1, c2 = st.columns(2)
        with c1:
            home = st.selectbox("Home Team", ALL_TEAMS,
                                key="entry_home")
            home_goals = st.number_input(
                "Home Goals", min_value=0,
                max_value=20, value=0)
        with c2:
            away = st.selectbox("Away Team", ALL_TEAMS,
                                key="entry_away",
                                index=1)
            away_goals = st.number_input(
                "Away Goals", min_value=0,
                max_value=20, value=0)

        if st.button("💾 Save Result", type="primary",
                     use_container_width=True):
            if home == away:
                st.error("Home and away must be different!")
            else:
                if save_result(home, away,
                               home_goals, away_goals):
                    st.session_state.results = load_results()
                    st.success(
                        f"✓ Saved: {home} "
                        f"{home_goals}-{away_goals} {away}"
                    )
                    st.rerun()

        # Current results
        st.markdown("---")
        st.markdown("### Results Entered")
        if live_results:
            for key, r in live_results.items():
                col1, col2 = st.columns([4, 1])
                with col1:
                    hg = r['home_score']
                    ag = r['away_score']
                    result_str = (
                        "🟢 HOME" if hg > ag else
                        "🔴 AWAY" if hg < ag else
                        "🟡 DRAW"
                    )
                    st.markdown(
                        f"{get_flag(r['home_team'])} "
                        f"**{r['home_team']}** "
                        f"{hg}–{ag} "
                        f"**{r['away_team']}** "
                        f"{get_flag(r['away_team'])} "
                        f"— {result_str}"
                    )
                with col2:
                    if st.button("🗑️", key=f"del_{key}"):
                        delete_result(r['home_team'],
                                      r['away_team'])
                        st.session_state.results = \
                            load_results()
                        st.rerun()
        else:
            st.info("No results entered yet.")

        if st.button("🚪 Logout"):
            st.session_state.admin_auth = False
            st.rerun()
