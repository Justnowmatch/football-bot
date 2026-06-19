import requests
import time
from flask import Flask
import threading

PAGE_ACCESS_TOKEN = "EAAN7Rz9InKsBRqav53KOOCjuJmdYwovWui4xqe4yWFZB5r6hVYzEpPIBrqojY0QuCUjbii7CISkMwDx7TKY3bRf021KnotRKZBLZBHy5K1SSeKL6eZCqwVHcvCIxU68SeP8TWB7XGIBdyGms9T5cObfIPQ6XAz7SgPQQ1f51Y8Pugi2DSpPxBLsUd7o0WZAUBk6SPDNvNJce1ZBoeqFKxfz10tS8glc8SoEEGm0tWOatpbfcGy4A8q9cd2mRwZD"
PAGE_ID = "597444063788593"
API_FOOTBALL_KEY = "1599bfe4913ab81c50a4d659fe5ca1cf"

LEAGUE_IDS = [39,140,135,78,61,88,94,144,203,179,253,307,1]

posted_goals = set()
posted_redcards = set()
posted_halftime = set()
posted_fulltime = set()

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

def get_live_scores():
    url = "https://v3.football.api-sports.io/fixtures?live=all"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    response = requests.get(url, headers=headers)
    return response.json()

def get_standings(league_id, season):
    url = f"https://v3.football.api-sports.io/standings?league={league_id}&season={season}"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    response = requests.get(url, headers=headers)
    return response.json()

def post_to_facebook(message):
    url = "https://graph.facebook.com/" + PAGE_ID + "/feed"
    payload = {"message": message, "access_token": PAGE_ACCESS_TOKEN}
    response = requests.post(url, data=payload)
    return response.json()

def run_bot():
    print("Bot is running...", flush=True)
    while True:
        print("Loop tick - checking matches...", flush=True)
        try:
            data = get_live_scores()
            print("Matches found:", len(data.get("response", [])), flush=True)
            print("Raw API response:", data, flush=True)

            for fixture in data.get("response", []):
                league_id_check = fixture["league"]["id"]
                print("Checking league id:", league_id_check, "-", fixture["league"]["name"], flush=True)

                if league_id_check not in LEAGUE_IDS:
                    continue

                fid = fixture["fixture"]["id"]
                home = fixture["teams"]["home"]["name"]
                away = fixture["teams"]["away"]["name"]
                hs = fixture["goals"]["home"]
                as_ = fixture["goals"]["away"]
                minute = fixture["fixture"]["status"]["elapsed"]
                status = fixture["fixture"]["status"]["short"]
                league = fixture["league"]["name"]
                league_id = fixture["league"]["id"]
                season = fixture["league"]["season"]
                events = fixture.get("events", [])

                print(f"Match: {home} {hs}-{as_} {away} | Status: {status} | Minute: {minute}", flush=True)

                goal_key = f"{fid}_{hs}_{as_}"
                if goal_key not in posted_goals:
                    scorers = [e for e in events if e["type"] == "Goal"]
                    scorer_text = ""
                    if scorers:
                        last = scorers[-1]
                        scorer_text = f"\n⚽ {last['player']['name']} {last['time']['elapsed']}'"
                    msg = f"JUST NOW ⚽\n\n{league}\n\n{home} {hs} - {as_} {away}{scorer_text}\n\n⏱️ {minute}'\n\n#Football #LiveScore #JustNowMatch"
                    post_to_facebook(msg)
                    print("Goal posted:", msg, flush=True)
                    posted_goals.add(goal_key)

                redcards = [e for e in events if e["type"] == "Card" and e["detail"] == "Red Card"]
                for card in redcards:
                    card_key = f"{fid}_red_{card['player']['name']}_{card['time']['elapsed']}"
                    if card_key not in posted_redcards:
                        msg = f"🟥 RED CARD!\n\n{league}\n\n{home} {hs} - {as_} {away}\n\n🟥 {card['player']['name']} - {card['time']['elapsed']}'\n\n#Football #RedCard #JustNowMatch"
                        post_to_facebook(msg)
                        print("Red card posted:", msg, flush=True)
                        posted_redcards.add(card_key)

                if status == "HT" and fid not in posted_halftime:
                    msg = f"⏱️ HALF TIME!\n\n{league}\n\n{home} {hs} - {as_} {away}\n\n#Football #HalfTime #JustNowMatch"
                    post_to_facebook(msg)
                    print("HT posted:", msg, flush=True)
                    posted_halftime.add(fid)

                if status == "FT" and fid not in posted_fulltime:
                    ft_scorers = [e for e in events if e["type"] == "Goal"]
                    scorers_text = ""
                    for g in ft_scorers:
                        scorers_text += f"\n⚽ {g['player']['name']} {g['time']['elapsed']}'"

                    standings_text = ""
                    try:
                        standings_data = get_standings(league_id, season)
                        standings = standings_data["response"][0]["league"]["standings"][0][:6]
                        standings_text = "\n\n📊 TOP 6 STANDINGS:\n"
                        for team in standings:
                            pos = team["rank"]
                            name = team["team"]["name"]
                            pts = team["points"]
                            standings_text += f"{pos}. {name} — {pts}pts\n"
                    except:
                        pass

                    msg = f"🏁 FULL TIME!\n\n{league}\n\n{home} {hs} - {as_} {away}\n{scorers_text}{standings_text}\n#Football #FullTime #JustNowMatch"
                    post_to_facebook(msg)
                    print("FT posted:", msg, flush=True)
                    posted_fulltime.add(fid)

        except Exception as e:
            print("Error:", e, flush=True)

        time.sleep(60)
