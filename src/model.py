import numpy as np
import pandas as pd
from scipy.stats import poisson

FEATURES = [
    'elo_diff', 'home_form_gd', 'away_form_gd',
    'home_form_wins', 'away_form_wins',
    'home_form_gf', 'away_form_gf',
    'home_form_ga', 'away_form_ga'
]

def get_live_form(team, results_dict, n=5):
    """Compute form stats from live results."""
    team_results = []
    for key, r in results_dict.items():
        if r['home_team'] == team:
            team_results.append({
                'gf': r['home_score'], 'ga': r['away_score'],
                'win': r['home_score'] > r['away_score'],
                'draw': r['home_score'] == r['away_score'],
                'loss': r['home_score'] < r['away_score'],
            })
        elif r['away_team'] == team:
            team_results.append({
                'gf': r['away_score'], 'ga': r['home_score'],
                'win': r['away_score'] > r['home_score'],
                'draw': r['away_score'] == r['home_score'],
                'loss': r['away_score'] < r['home_score'],
            })

    recent = team_results[-n:]
    if not recent:
        return {'form_wins': 0, 'form_draws': 0, 'form_losses': 0,
                'form_gf': 0, 'form_ga': 0, 'form_gd': 0}

    return {
        'form_wins'  : sum(r['win']  for r in recent),
        'form_draws' : sum(r['draw'] for r in recent),
        'form_losses': sum(r['loss'] for r in recent),
        'form_gf'    : sum(r['gf']   for r in recent),
        'form_ga'    : sum(r['ga']   for r in recent),
        'form_gd'    : sum(r['gf'] - r['ga'] for r in recent),
    }


def predict_match(home_team, away_team, team_strength_df,
                  model_home, model_away, scaler,
                  live_results=None, max_goals=6):
    """Full match prediction with probabilities."""
    home_row = team_strength_df[team_strength_df['team'] == home_team]
    away_row = team_strength_df[team_strength_df['team'] == away_team]

    if len(home_row) == 0 or len(away_row) == 0:
        return None

    elo_home = home_row['blended_elo'].values[0]
    elo_away = away_row['blended_elo'].values[0]
    elo_diff = elo_home - elo_away

    hf = get_live_form(home_team, live_results or {})
    af = get_live_form(away_team, live_results or {})

    feat = pd.DataFrame([[
        elo_diff,
        hf['form_gd'], af['form_gd'],
        hf['form_wins'], af['form_wins'],
        hf['form_gf'], af['form_gf'],
        hf['form_ga'], af['form_ga'],
    ]], columns=FEATURES)

    feat_scaled = scaler.transform(feat)
    lambda_home = model_home.predict(feat_scaled)[0]
    lambda_away = model_away.predict(feat_scaled)[0]

    # Scoreline probability matrix
    score_matrix = np.zeros((max_goals+1, max_goals+1))
    for i in range(max_goals+1):
        for j in range(max_goals+1):
            score_matrix[i][j] = (poisson.pmf(i, lambda_home) *
                                  poisson.pmf(j, lambda_away))

    prob_home = float(np.sum(np.tril(score_matrix, -1)))
    prob_draw = float(np.sum(np.diag(score_matrix)))
    prob_away = float(np.sum(np.triu(score_matrix,  1)))
    idx       = np.unravel_index(score_matrix.argmax(), score_matrix.shape)

    # Top 5 scorelines
    flat    = score_matrix.flatten()
    top5idx = flat.argsort()[-5:][::-1]
    top5    = [(divmod(i, max_goals+1), float(flat[i])) for i in top5idx]

    return {
        'home_team'      : home_team,
        'away_team'      : away_team,
        'elo_home'       : round(elo_home, 1),
        'elo_away'       : round(elo_away, 1),
        'lambda_home'    : round(lambda_home, 3),
        'lambda_away'    : round(lambda_away, 3),
        'predicted_score': idx,
        'prob_home_win'  : round(prob_home, 3),
        'prob_draw'      : round(prob_draw, 3),
        'prob_away_win'  : round(prob_away, 3),
        'top5_scorelines': top5,
        'home_form'      : hf,
        'away_form'      : af,
    }
