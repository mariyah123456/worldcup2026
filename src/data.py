import pandas as pd
import streamlit as st
import urllib.request
import urllib.parse
import json

SHEET_ID = "1BkCnYwFkPx37zLOx82VHwwSBTLtm7zQfhquBl8Tlt5o"
SHEET_NAME = "Sheet1"


def load_results():
    try:
        url = (f"https://docs.google.com/spreadsheets/d/"
               f"{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}")
        df = pd.read_csv(url)
        df.columns = ['home_team', 'away_team',
                      'home_score', 'away_score']
        df = df.dropna(subset=['home_team', 'away_team'])
        results = {}
        for _, row in df.iterrows():
            round_val = str(row['round']) if 'round' in row.index else 'Group stage'
            key = f"{row['home_team']}_vs_{row['away_team']}_{round_val}"
            results[key] = {
                'home_team' : str(row['home_team']),
                'away_team' : str(row['away_team']),
                'home_score': int(row['home_score']),
                'away_score': int(row['away_score']),
            }
        return results
    except Exception as e:
        st.error(f"Error loading results: {e}")
        return {}


def save_result(home_team, away_team, home_score, away_score, round_name='Group stage'):
    try:
        # Load existing results
        results = load_results()
        round_val = str(row['round']) if 'round' in df.columns else 'Group stage'
        key = f"{row['home_team']}_vs_{row['away_team']}_{row.get('round', 'Group stage')}"

        # Check if already exists
        if key in results:
            # Update via Apps Script
            _update_sheet(home_team, away_team,
                         home_score, away_score, update=True)
        else:
            _update_sheet(home_team, away_team,
                         home_score, away_score, update=False)
        return True
    except Exception as e:
        st.error(f"Error saving result: {e}")
        return False


def _update_sheet(home_team, away_team,
                  home_score, away_score, update=False):
    """Use Google Apps Script to write to sheet."""
    apps_script_url = st.secrets.get("APPS_SCRIPT_URL", "")
    if not apps_script_url:
        st.error("Apps Script URL not configured")
        return False

    payload = json.dumps({
        'home_team' : home_team,
        'away_team' : away_team,
        'home_score': int(home_score),
        'away_score': int(away_score),
        'round'     : round_name,
        'update'    : update
    }).encode('utf-8')

    req = urllib.request.Request(
        apps_script_url,
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req) as response:
        return True


def delete_result(home_team, away_team):
    try:
        apps_script_url = st.secrets.get("APPS_SCRIPT_URL", "")
        if not apps_script_url:
            return False
        payload = json.dumps({
            'home_team': home_team,
            'away_team': away_team,
            'delete'   : True
        }).encode('utf-8')
        req = urllib.request.Request(
            apps_script_url,
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req) as response:
            return True
    except Exception as e:
        st.error(f"Error deleting result: {e}")
        return False


def get_group_standings(live_results, groups):
    all_standings = {}
    for group, teams in groups.items():
        table = {t: {'W':0,'D':0,'L':0,'GF':0,'GA':0,'Pts':0}
                 for t in teams}
        for key, r in live_results.items():
            home = r['home_team']
            away = r['away_team']
            hg   = r['home_score']
            ag   = r['away_score']
            if home not in table or away not in table:
                continue
            table[home]['GF'] += hg; table[home]['GA'] += ag
            table[away]['GF'] += ag; table[away]['GA'] += hg
            if hg > ag:
                table[home]['W']+=1; table[home]['Pts']+=3
                table[away]['L']+=1
            elif hg < ag:
                table[away]['W']+=1; table[away]['Pts']+=3
                table[home]['L']+=1
            else:
                table[home]['D']+=1; table[home]['Pts']+=1
                table[away]['D']+=1; table[away]['Pts']+=1
        df = pd.DataFrame(table).T
        df['GD'] = df['GF'] - df['GA']
        df = df.sort_values(['Pts','GD','GF'], ascending=False)
        all_standings[group] = df
    return all_standings
