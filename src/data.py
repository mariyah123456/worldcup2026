import pandas as pd
import streamlit as st
import urllib.request
import urllib.error
import json


def get_credentials():
    url = str(st.secrets["SUPABASE_URL"]).strip()
    key = str(st.secrets["SUPABASE_KEY"]).strip()
    return url, key


def load_results():
    try:
        url, key = get_credentials()
        endpoint = f"{url}/rest/v1/results?select=*"
        req = urllib.request.Request(
            endpoint,
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
        results = {}
        for row in data:
            k = f"{row['home_team']}_vs_{row['away_team']}"
            results[k] = {
                'home_team' : row['home_team'],
                'away_team' : row['away_team'],
                'home_score': row['home_score'],
                'away_score': row['away_score'],
            }
        return results
    except Exception as e:
        st.error(f"Error loading results: {e}")
        return {}


def save_result(home_team, away_team, home_score, away_score):
    try:
        url, key = get_credentials()
        endpoint = f"{url}/rest/v1/results"
        payload = json.dumps({
            'home_team' : home_team,
            'away_team' : away_team,
            'home_score': int(home_score),
            'away_score': int(away_score),
        }).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=payload,
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates"
            },
            method="POST"
        )
        with urllib.request.urlopen(req) as response:
            return True
    except Exception as e:
        st.error(f"Error saving result: {e}")
        return False


def delete_result(home_team, away_team):
    try:
        url, key = get_credentials()
        endpoint = (f"{url}/rest/v1/results"
                    f"?home_team=eq.{urllib.parse.quote(home_team)}"
                    f"&away_team=eq.{urllib.parse.quote(away_team)}")
        import urllib.parse
        req = urllib.request.Request(
            endpoint,
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            },
            method="DELETE"
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
