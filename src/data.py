import pandas as pd
import streamlit as st
import urllib.request
import urllib.parse
import json


def get_credentials():
    bin_id = st.secrets["JSONBIN_BIN_ID"]
    api_key = st.secrets["JSONBIN_API_KEY"]
    return bin_id, api_key


def load_results():
    try:
        bin_id, api_key = get_credentials()
        url = f"https://api.jsonbin.io/v3/b/{bin_id}/latest"
        req = urllib.request.Request(
            url,
            headers={
                "X-Master-Key": api_key,
                "X-Bin-Meta": "false"
            }
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(
                response.read().decode("utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception as e:
        st.error(f"Error loading results: {e}")
        return {}


def save_result(home_team, away_team,
                home_score, away_score):
    try:
        # Load current results
        results = load_results()

        # Add new result
        key = f"{home_team}_vs_{away_team}"
        results[key] = {
            'home_team' : home_team,
            'away_team' : away_team,
            'home_score': int(home_score),
            'away_score': int(away_score),
        }

        # Save back
        bin_id, api_key = get_credentials()
        url = f"https://api.jsonbin.io/v3/b/{bin_id}"
        payload = json.dumps(results).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "X-Master-Key": api_key,
                "Content-Type": "application/json"
            },
            method="PUT"
        )
        with urllib.request.urlopen(req) as response:
            return True
    except Exception as e:
        st.error(f"Error saving result: {e}")
        return False


def delete_result(home_team, away_team):
    try:
        results = load_results()
        key = f"{home_team}_vs_{away_team}"
        if key in results:
            del results[key]

        bin_id, api_key = get_credentials()
        url = f"https://api.jsonbin.io/v3/b/{bin_id}"
        payload = json.dumps(results).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "X-Master-Key": api_key,
                "Content-Type": "application/json"
            },
            method="PUT"
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
        df = df.sort_values(['Pts','GD','GF'],
                            ascending=False)
        all_standings[group] = df

    return all_standings
