import numpy as np
import pandas as pd
from scipy.stats import poisson
from src.groups import GROUPS
from src.model import get_live_form, FEATURES


def simulate_match(home_team, away_team, team_strength_df,
    model_home, model_away, scaler, form_dict=None):
    home_row = team_strength_df[team_strength_df['team'] == home_team]
    away_row = team_strength_df[team_strength_df['team'] == away_team]
    if len(home_row) == 0 or len(away_row) == 0:
        return 1, 1

    elo_diff = (home_row['blended_elo'].values[0] -
                away_row['blended_elo'].values[0])

    hf = form_dict.get(home_team, {}) if form_dict else {}
    af = form_dict.get(away_team, {}) if form_dict else {}

    feat = pd.DataFrame([[
        elo_diff,
        hf.get('form_gd', 0), af.get('form_gd', 0),
        hf.get('form_wins', 0), af.get('form_wins', 0),
        hf.get('form_gf', 0), af.get('form_gf', 0),
        hf.get('form_ga', 0), af.get('form_ga', 0),
    ]], columns=FEATURES)

    lh = model_home.predict(scaler.transform(feat))[0]
    la = model_away.predict(scaler.transform(feat))[0]
    return int(np.random.poisson(lh)), int(np.random.poisson(la))


def simulate_knockout(home, away, team_strength_df,
                      model_home, model_away, scaler, form_dict=None):
    hg, ag = simulate_match(home, away, team_strength_df,
                             model_home, model_away, scaler, form_dict)
    if hg == ag:
        h_elo = team_strength_df[
            team_strength_df['team'] == home]['blended_elo'].values[0]
        a_elo = team_strength_df[
            team_strength_df['team'] == away]['blended_elo'].values[0]
        return home if np.random.random() < 0.5 + (h_elo-a_elo)*0.0001 \
               else away
    return home if hg > ag else away

def run_simulation(team_strength_df, model_home, model_away,
                   scaler, live_results, n_sims=500,
                   progress_bar=None):
    """Run full tournament simulation."""
    all_teams = [t for teams in GROUPS.values() for t in teams]
    form_dict = {t: get_live_form(t, live_results) for t in all_teams}

    win_counts      = {}
    finalist_counts = {}
    sf_counts       = {}
    qualify_counts  = {}

    for i in range(n_sims):

        # Update progress bar every 50 sims
        if progress_bar is not None and i % 50 == 0:
            progress = int(i / n_sims * 100)
            progress_bar.progress(
                progress,
                text=f"Running simulations... {progress}%"
            )

        standings = {}
        for group, teams in GROUPS.items():
            table = {t: {'W':0,'D':0,'L':0,'GF':0,'GA':0,'Pts':0}
                     for t in teams}

            for a in range(len(teams)):
                for b in range(a+1, len(teams)):
                    home, away = teams[a], teams[b]

                    # Check all key formats
                    key1 = f"{home}_vs_{away}_Group stage"
                    key2 = f"{away}_vs_{home}_Group stage"
                    key3 = f"{home}_vs_{away}"
                    key4 = f"{away}_vs_{home}"

                    if key1 in live_results:
                        hg = live_results[key1]['home_score']
                        ag = live_results[key1]['away_score']
                    elif key2 in live_results:
                        ag = live_results[key2]['home_score']
                        hg = live_results[key2]['away_score']
                    elif key3 in live_results:
                        hg = live_results[key3]['home_score']
                        ag = live_results[key3]['away_score']
                    elif key4 in live_results:
                        ag = live_results[key4]['home_score']
                        hg = live_results[key4]['away_score']
                    else:
                        hg, ag = simulate_match(
                            home, away, team_strength_df,
                            model_home, model_away,
                            scaler, form_dict)

                    table[home]['GF'] += hg
                    table[home]['GA'] += ag
                    table[away]['GF'] += ag
                    table[away]['GA'] += hg

                    if hg > ag:
                        table[home]['W'] += 1
                        table[home]['Pts'] += 3
                        table[away]['L'] += 1
                    elif hg < ag:
                        table[away]['W'] += 1
                        table[away]['Pts'] += 3
                        table[home]['L'] += 1
                    else:
                        table[home]['D'] += 1
                        table[home]['Pts'] += 1
                        table[away]['D'] += 1
                        table[away]['Pts'] += 1

            df = pd.DataFrame(table).T
            df['GD'] = df['GF'] - df['GA']
            standings[group] = df.sort_values(
                ['Pts','GD','GF'], ascending=False)

        # Qualifiers
        top2   = []
        thirds = []
        for group, df in standings.items():
            top2.extend([df.index[0], df.index[1]])
            thirds.append((df.index[2],
                           df.iloc[2]['Pts'],
                           df.iloc[2]['GD'],
                           df.iloc[2]['GF']))

        best8      = sorted(thirds,
                            key=lambda x: (x[1],x[2],x[3]),
                            reverse=True)[:8]
        qualifiers = top2 + [t[0] for t in best8]

        for t in qualifiers:
            qualify_counts[t] = qualify_counts.get(t, 0) + 1

        # Knockout rounds
        teams = qualifiers.copy()
        np.random.shuffle(teams)

        r16 = [simulate_knockout(
                    teams[i], teams[i+1], team_strength_df,
                    model_home, model_away, scaler, form_dict)
               for i in range(0, 32, 2)]

        qf  = [simulate_knockout(
                    r16[i], r16[i+1], team_strength_df,
                    model_home, model_away, scaler, form_dict)
               for i in range(0, 16, 2)]

        sf  = [simulate_knockout(
                    qf[i], qf[i+1], team_strength_df,
                    model_home, model_away, scaler, form_dict)
               for i in range(0, 8, 2)]

        for t in sf:
            sf_counts[t] = sf_counts.get(t, 0) + 1

        f = [simulate_knockout(
                 sf[i], sf[i+1], team_strength_df,
                 model_home, model_away, scaler, form_dict)
             for i in range(0, 4, 2)]

        for t in f:
            finalist_counts[t] = finalist_counts.get(t, 0) + 1

        champ = simulate_knockout(
            f[0], f[1], team_strength_df,
            model_home, model_away, scaler, form_dict)
        win_counts[champ] = win_counts.get(champ, 0) + 1

    # Final progress
    if progress_bar is not None:
        progress_bar.progress(100, text="Done!")

    # Build results dataframe
    all_team_set = set(list(win_counts.keys()) +
                       list(qualify_counts.keys()))
    results = []
    for team in all_team_set:
        results.append({
            'team'      : team,
            'win_%'     : round(win_counts.get(team,0)      / n_sims * 100, 1),
            'final_%'   : round(finalist_counts.get(team,0) / n_sims * 100, 1),
            'semi_%'    : round(sf_counts.get(team,0)       / n_sims * 100, 1),
            'qualify_%' : round(qualify_counts.get(team,0)  / n_sims * 100, 1),
        })

    return pd.DataFrame(results).sort_values(
        'win_%', ascending=False).reset_index(drop=True)

        # Qualifiers
        top2   = []
        thirds = []
        for group, df in standings.items():
            top2.extend([df.index[0], df.index[1]])
            thirds.append((df.index[2],
                           df.iloc[2]['Pts'],
                           df.iloc[2]['GD'],
                           df.iloc[2]['GF']))

        best8      = sorted(thirds,
                            key=lambda x: (x[1],x[2],x[3]),
                            reverse=True)[:8]
        qualifiers = top2 + [t[0] for t in best8]

        for t in qualifiers:
            qualify_counts[t] = qualify_counts.get(t, 0) + 1

        # Knockout rounds
        teams = qualifiers.copy()
        np.random.shuffle(teams)

        r16 = [simulate_knockout(teams[i], teams[i+1], team_strength_df,
                                 model_home, model_away, scaler, form_dict)
               for i in range(0, 32, 2)]
        qf  = [simulate_knockout(r16[i], r16[i+1], team_strength_df,
                                 model_home, model_away, scaler, form_dict)
               for i in range(0, 16, 2)]
        sf  = [simulate_knockout(qf[i], qf[i+1], team_strength_df,
                                 model_home, model_away, scaler, form_dict)
               for i in range(0, 8, 2)]

        for t in sf:
            sf_counts[t] = sf_counts.get(t, 0) + 1

        f = [simulate_knockout(sf[i], sf[i+1], team_strength_df,
                               model_home, model_away, scaler, form_dict)
             for i in range(0, 4, 2)]

        for t in f:
            finalist_counts[t] = finalist_counts.get(t, 0) + 1

        champ = simulate_knockout(f[0], f[1], team_strength_df,
                                  model_home, model_away, scaler, form_dict)
        win_counts[champ] = win_counts.get(champ, 0) + 1

    # Build results dataframe
    all_team_set = set(list(win_counts.keys()) +
                       list(qualify_counts.keys()))
    results = []
    for team in all_team_set:
        results.append({
            'team'      : team,
            'win_%'     : round(win_counts.get(team,0)      / n_sims * 100, 1),
            'final_%'   : round(finalist_counts.get(team,0) / n_sims * 100, 1),
            'semi_%'    : round(sf_counts.get(team,0)       / n_sims * 100, 1),
            'qualify_%' : round(qualify_counts.get(team,0)  / n_sims * 100, 1),
        })

    return pd.DataFrame(results).sort_values(
        'win_%', ascending=False).reset_index(drop=True)
