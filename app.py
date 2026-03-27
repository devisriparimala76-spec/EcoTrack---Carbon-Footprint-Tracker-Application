"""
EcoTrack v3.0 — Intelligent Carbon Footprint Tracker
Hackathon-Grade | AI-Powered | Real-Time News | Gamified
"""

import streamlit as st
import sqlite3
import hashlib
import json
import random
import math
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, date
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EcoTrack — Carbon Footprint Tracker",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Constants ─────────────────────────────────────────────────────────────────
REGION_CONFIG = {
    "India": {
        "electricity_factor": 0.82,
        "car_factor": 0.21,
        "bus_factor": 0.089,
        "train_factor": 0.041,
        "ev_kwh_per_km": 0.18,
        "moto_factor": 0.113,
        "flag": "🇮🇳",
        "grid_label": "Coal-Heavy Grid",
        "avg_daily_co2": 11.5,
        "currency": "₹",
    },
    "USA": {
        "electricity_factor": 0.386,
        "car_factor": 0.267,
        "bus_factor": 0.089,
        "train_factor": 0.028,
        "ev_kwh_per_km": 0.21,
        "moto_factor": 0.103,
        "flag": "🇺🇸",
        "grid_label": "Mixed Sources",
        "avg_daily_co2": 12.9,
        "currency": "$",
    },
    "UK": {
        "electricity_factor": 0.233,
        "car_factor": 0.170,
        "bus_factor": 0.079,
        "train_factor": 0.035,
        "ev_kwh_per_km": 0.17,
        "moto_factor": 0.095,
        "flag": "🇬🇧",
        "grid_label": "Gas + Renewables",
        "avg_daily_co2": 8.7,
        "currency": "£",
    },
    "Germany": {
        "electricity_factor": 0.366,
        "car_factor": 0.162,
        "bus_factor": 0.079,
        "train_factor": 0.029,
        "ev_kwh_per_km": 0.17,
        "moto_factor": 0.091,
        "flag": "🇩🇪",
        "grid_label": "Transitioning Grid",
        "avg_daily_co2": 9.4,
        "currency": "€",
    },
    "Australia": {
        "electricity_factor": 0.79,
        "car_factor": 0.192,
        "bus_factor": 0.089,
        "train_factor": 0.026,
        "ev_kwh_per_km": 0.20,
        "moto_factor": 0.100,
        "flag": "🇦🇺",
        "grid_label": "Coal-Heavy Grid",
        "avg_daily_co2": 13.8,
        "currency": "A$",
    },
    "Global Average": {
        "electricity_factor": 0.475,
        "car_factor": 0.210,
        "bus_factor": 0.089,
        "train_factor": 0.041,
        "ev_kwh_per_km": 0.19,
        "moto_factor": 0.103,
        "flag": "🌍",
        "grid_label": "Global Avg",
        "avg_daily_co2": 12.9,
        "currency": "$",
    },
}

FOOD_EMISSIONS = {
    "Vegan": 1.5,
    "Vegetarian": 2.5,
    "Flexitarian (some meat)": 4.5,
    "Regular (meat daily)": 7.0,
    "Heavy Meat Eater": 10.5,
}

ELECTRICITY_SOURCES = {
    "Grid (Standard)": 1.0,
    "Mixed (Some Solar)": 0.55,
    "Mostly Solar / Renewable": 0.15,
    "Fully Solar / Green Tariff": 0.03,
}

TRANSPORT_MODES = {
    "Personal Car (Petrol)": "car",
    "Personal Car (Diesel)": "diesel",
    "Personal Car (EV)": "ev",
    "Public Bus": "bus",
    "Metro / Train": "train",
    "Motorcycle / Scooter": "moto",
    "Bicycle / Walking": "zero",
}

BADGES = [
    {"id": "beginner",    "name": "🌱 Beginner",      "desc": "Logged first entry",            "threshold": 1},
    {"id": "consistent",  "name": "📅 Consistent",     "desc": "7-day logging streak",          "threshold": 7},
    {"id": "eco_warrior", "name": "🌿 Eco Warrior",    "desc": "30 entries logged",             "threshold": 30},
    {"id": "low_carbon",  "name": "💚 Low Carbon",     "desc": "Avg below 15 kg CO₂/day",       "threshold": 15},
    {"id": "green_star",  "name": "⭐ Green Star",     "desc": "Avg below 10 kg CO₂/day",       "threshold": 10},
    {"id": "climate_hero","name": "🌍 Climate Hero",   "desc": "Avg below 5.5 kg CO₂/day",      "threshold": 5.5},
    {"id": "streak_30",   "name": "🔥 30-Day Streak",  "desc": "30-day consecutive logging",    "threshold": 30},
    {"id": "centurion",   "name": "💯 Centurion",      "desc": "100 entries logged",             "threshold": 100},
]

# ─── Database ──────────────────────────────────────────────────────────────────
def get_conn():
    return sqlite3.connect("ecotrack.db", check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        region TEXT DEFAULT 'India',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS carbon_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        region TEXT DEFAULT 'India',
        log_date TEXT DEFAULT (date('now')),
        travel_km REAL DEFAULT 0,
        transport_mode TEXT DEFAULT 'Personal Car (Petrol)',
        electricity_units REAL DEFAULT 0,
        electricity_source TEXT DEFAULT 'Grid (Standard)',
        water_usage INTEGER DEFAULT 3,
        waste_bags INTEGER DEFAULT 1,
        plastic_level INTEGER DEFAULT 2,
        food_type TEXT DEFAULT 'Vegetarian',
        shopping_level INTEGER DEFAULT 2,
        flights_per_year REAL DEFAULT 0,
        total_co2 REAL DEFAULT 0,
        impact_score REAL DEFAULT 0,
        travel_co2 REAL DEFAULT 0,
        electricity_co2 REAL DEFAULT 0,
        food_co2 REAL DEFAULT 0,
        lifestyle_co2 REAL DEFAULT 0,
        flight_co2 REAL DEFAULT 0,
        logged_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS ai_conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY,
        gemini_api_key TEXT DEFAULT '',
        newsapi_key TEXT DEFAULT '',
        openai_api_key TEXT DEFAULT '',
        FOREIGN KEY (user_id) REFERENCES users(id)
    )""")

    # Migrations
    _migrate(c, "carbon_logs", {
        "log_date": "TEXT DEFAULT (date('now'))",
        "electricity_source": "TEXT DEFAULT 'Grid (Standard)'",
        "water_usage": "INTEGER DEFAULT 3",
        "waste_bags": "INTEGER DEFAULT 1",
        "lifestyle_co2": "REAL DEFAULT 0",
    })
    _migrate(c, "users", {"region": "TEXT DEFAULT 'India'"})

    conn.commit()
    conn.close()

def _migrate(c, table, cols):
    existing = {row[1] for row in c.execute(f"PRAGMA table_info({table})").fetchall()}
    for col, defn in cols.items():
        if col not in existing:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {defn}")

def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

def create_user(username, email, password, region):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username,email,password,region) VALUES (?,?,?,?)",
                  (username, email, hash_pw(password), region))
        uid = c.lastrowid
        c.execute("INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)", (uid,))
        conn.commit()
        return True, "Account created!"
    except sqlite3.IntegrityError as e:
        return False, "Username or email already exists."
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id,username,region FROM users WHERE username=? AND password=?",
              (username, hash_pw(password)))
    row = c.fetchone()
    conn.close()
    return row

def save_log(user_id, region, log_date, travel_km, transport_mode, electricity_units,
             electricity_source, water_usage, waste_bags, plastic_level, food_type,
             shopping_level, flights_per_year, total_co2, impact_score, bd):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO carbon_logs
        (user_id,region,log_date,travel_km,transport_mode,electricity_units,
         electricity_source,water_usage,waste_bags,plastic_level,food_type,
         shopping_level,flights_per_year,total_co2,impact_score,
         travel_co2,electricity_co2,food_co2,lifestyle_co2,flight_co2)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
              (user_id, region, log_date, travel_km, transport_mode, electricity_units,
               electricity_source, water_usage, waste_bags, plastic_level, food_type,
               shopping_level, flights_per_year, total_co2, impact_score,
               bd.get("Travel", 0), bd.get("Electricity", 0),
               bd.get("Food", 0), bd.get("Lifestyle", 0), bd.get("Flights", 0)))
    conn.commit()
    conn.close()

def get_logs(user_id):
    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT * FROM carbon_logs WHERE user_id=? ORDER BY log_date DESC, logged_at DESC",
        conn, params=(user_id,))
    conn.close()
    return df

def get_leaderboard():
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT u.username, u.region,
               COUNT(c.id) AS entries,
               AVG(c.total_co2) AS avg_co2,
               MIN(c.total_co2) AS best_day,
               MAX(c.log_date) AS last_log
        FROM users u JOIN carbon_logs c ON u.id=c.user_id
        GROUP BY u.id HAVING COUNT(c.id)>=1 ORDER BY avg_co2 ASC
    """, conn)
    conn.close()
    return df

def get_user_settings(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT gemini_api_key, newsapi_key, openai_api_key FROM user_settings WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"gemini": row[0] or "", "newsapi": row[1] or "", "openai": row[2] or ""}
    return {"gemini": "", "newsapi": "", "openai": ""}

def save_user_settings(user_id, gemini_key, newsapi_key, openai_key):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO user_settings (user_id, gemini_api_key, newsapi_key, openai_api_key)
                 VALUES (?,?,?,?)
                 ON CONFLICT(user_id) DO UPDATE SET
                 gemini_api_key=excluded.gemini_api_key,
                 newsapi_key=excluded.newsapi_key,
                 openai_api_key=excluded.openai_api_key""",
              (user_id, gemini_key, newsapi_key, openai_key))
    conn.commit()
    conn.close()

def save_ai_message(user_id, role, content):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO ai_conversations (user_id,role,content) VALUES (?,?,?)",
              (user_id, role, content))
    conn.commit()
    conn.close()

def get_ai_history(user_id, limit=20):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT role,content FROM ai_conversations WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
              (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return list(reversed(rows))

def clear_ai_history(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM ai_conversations WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

# ─── Carbon Calculation Engine ─────────────────────────────────────────────────
def calculate_carbon(region, travel_km, transport_mode, electricity_units,
                     electricity_source, water_usage, waste_bags, plastic_level,
                     food_type, shopping_level, flights_per_year):
    cfg = REGION_CONFIG[region]
    mode = TRANSPORT_MODES.get(transport_mode, "car")
    grid = cfg["electricity_factor"]

    # Transport
    factors = {
        "car": cfg["car_factor"],
        "diesel": cfg["car_factor"] * 1.05,
        "ev": cfg["ev_kwh_per_km"] * grid,
        "bus": cfg["bus_factor"],
        "train": cfg["train_factor"],
        "moto": cfg["moto_factor"],
        "zero": 0.0,
    }
    travel_co2 = travel_km * factors.get(mode, cfg["car_factor"])

    # Electricity with source multiplier
    src_mult = ELECTRICITY_SOURCES.get(electricity_source, 1.0)
    electricity_co2 = electricity_units * grid * src_mult

    # Food
    food_co2 = FOOD_EMISSIONS.get(food_type, 2.5)

    # Lifestyle: plastic + shopping + water + waste
    plastic_co2  = (plastic_level - 1) * 1.8          # 0–7.2 kg
    shopping_co2 = (shopping_level - 1) * 2.5          # 0–10 kg
    water_co2    = water_usage * 0.3                    # litres × factor
    waste_co2    = waste_bags * 2.1                     # bags/day
    lifestyle_co2 = plastic_co2 + shopping_co2 + water_co2 + waste_co2

    # Flights (annualised to daily)
    flight_co2 = (flights_per_year * 255) / 365        # 255 kg per flight avg

    total = travel_co2 + electricity_co2 + food_co2 + lifestyle_co2 + flight_co2
    impact_score = min(100, (total / 60) * 100)

    breakdown = {
        "Travel": round(travel_co2, 3),
        "Electricity": round(electricity_co2, 3),
        "Food": round(food_co2, 3),
        "Lifestyle": round(lifestyle_co2, 3),
        "Flights": round(flight_co2, 3),
    }

    # Smart tips
    tips = []
    regional_avg = cfg["avg_daily_co2"]
    if mode == "car" and travel_km > 15:
        save = travel_km * (cfg["car_factor"] - cfg["bus_factor"])
        tips.append(f"🚌 Take public transit for your {travel_km:.0f}km commute → save **{save:.1f}kg CO₂/day** ({save*365:.0f}kg/year).")
    if mode == "ev":
        tips.append(f"⚡ Your EV is great! Pairing it with solar reduces its {region} grid footprint by up to 97%.")
    if electricity_units > 10 and src_mult > 0.5:
        save_sol = electricity_units * grid * 0.85
        tips.append(f"☀️ Going solar eliminates ~{save_sol:.1f}kg CO₂/day from your electricity — payback in 5–7 years.")
    if food_type in ["Regular (meat daily)", "Heavy Meat Eater"]:
        diff = FOOD_EMISSIONS[food_type] - FOOD_EMISSIONS["Flexitarian (some meat)"]
        tips.append(f"🥗 Cutting meat to 3 days/week saves **{diff*365:.0f}kg CO₂/year** — same as not driving for {diff*365/cfg['car_factor']/20:.0f} months.")
    if waste_bags >= 2:
        tips.append("🗑️ Composting organic waste cuts landfill methane by 50% and reduces your waste footprint significantly.")
    if flights_per_year > 3:
        tips.append(f"✈️ {flights_per_year:.0f} flights/year = {flight_co2*365:.0f}kg CO₂. Consider rail for short trips — up to 96% less CO₂.")
    if shopping_level >= 4:
        tips.append("👕 Fast fashion emits 10% of global CO₂. Buying secondhand or renting can cut your fashion footprint by 80%.")
    if not tips:
        tips.append(f"🌟 Excellent! Your {total:.1f}kg/day is {'below' if total < regional_avg else 'near'} the {region} average of {regional_avg}kg. Keep it up!")

    vs_avg = ((total - regional_avg) / regional_avg) * 100
    return total, impact_score, tips, breakdown, vs_avg, regional_avg

# ─── Gamification Engine ───────────────────────────────────────────────────────
def compute_gamification(df):
    if df.empty:
        return {"streak": 0, "badges": [], "points": 0, "level": "🌱 Seedling", "next_badge": BADGES[0]}

    entries = len(df)
    avg_co2 = df["total_co2"].mean() if not df.empty else 99

    # Streak calculation
    streak = 0
    if "log_date" in df.columns:
        dates = sorted(pd.to_datetime(df["log_date"]).dt.date.unique(), reverse=True)
        today = date.today()
        check = today
        for d in dates:
            if d == check or d == check - timedelta(days=1):
                if d != check:
                    check = d
                streak += 1
                check -= timedelta(days=1)
            else:
                break

    # Badges
    earned = []
    if entries >= 1:      earned.append(BADGES[0])  # Beginner
    if streak >= 7:       earned.append(BADGES[1])  # Consistent
    if entries >= 30:     earned.append(BADGES[2])  # Eco Warrior
    if avg_co2 <= 15:     earned.append(BADGES[3])  # Low Carbon
    if avg_co2 <= 10:     earned.append(BADGES[4])  # Green Star
    if avg_co2 <= 5.5:    earned.append(BADGES[5])  # Climate Hero
    if streak >= 30:      earned.append(BADGES[6])  # 30-day streak
    if entries >= 100:    earned.append(BADGES[7])  # Centurion

    # Points
    points = entries * 10 + streak * 25 + max(0, int((20 - avg_co2) * 5))

    # Level
    if points < 50:     level = "🌱 Seedling"
    elif points < 200:  level = "🌿 Sprout"
    elif points < 500:  level = "🌳 Eco Warrior"
    elif points < 1000: level = "🌍 Green Champion"
    else:               level = "⭐ Climate Hero"

    next_b = next((b for b in BADGES if b not in earned), None)
    return {"streak": streak, "badges": earned, "points": points, "level": level, "next_badge": next_b}

# ─── Smart Insights Engine ─────────────────────────────────────────────────────
def generate_insights(df, region):
    insights = []
    if len(df) < 2:
        return [{"type": "info", "icon": "💡", "text": "Log at least 2 days to unlock personalised insights."}]

    cfg = REGION_CONFIG[region]
    df = df.copy()
    df["log_date"] = pd.to_datetime(df["log_date"])
    df = df.sort_values("log_date")

    # Week-over-week
    if len(df) >= 14:
        last7  = df.tail(7)["total_co2"].mean()
        prev7  = df.iloc[-14:-7]["total_co2"].mean()
        change = ((last7 - prev7) / prev7) * 100
        icon   = "📉" if change < 0 else "📈"
        color  = "good" if change < 0 else "warn"
        insights.append({"type": color, "icon": icon,
                          "text": f"Your last 7-day avg is **{last7:.1f}kg/day** — {abs(change):.0f}% {'lower' if change < 0 else 'higher'} than the previous week."})

    # Best and worst day
    best = df.loc[df["total_co2"].idxmin()]
    worst = df.loc[df["total_co2"].idxmax()]
    insights.append({"type": "good", "icon": "🏆",
                      "text": f"Best day: **{best['total_co2']:.1f}kg** on {str(best['log_date'])[:10]}. Keep aiming for this!"})
    insights.append({"type": "warn", "icon": "⚠️",
                      "text": f"Highest day: **{worst['total_co2']:.1f}kg** on {str(worst['log_date'])[:10]}. What drove that spike?"})

    # Transport pattern
    if "transport_mode" in df.columns:
        mode_counts = df["transport_mode"].value_counts()
        if not mode_counts.empty:
            top_mode = mode_counts.index[0]
            if "Car" in top_mode and "EV" not in top_mode:
                car_co2 = df["travel_co2"].mean() if "travel_co2" in df.columns else 0
                insights.append({"type": "action", "icon": "🚗",
                                  "text": f"You drive most days (~{car_co2:.1f}kg CO₂/day). Switching to public transport twice a week saves ~{car_co2*2*52:.0f}kg/year."})

    # Electricity trend
    if "electricity_co2" in df.columns and df["electricity_co2"].mean() > 5:
        avg_e = df["electricity_co2"].mean()
        insights.append({"type": "action", "icon": "⚡",
                          "text": f"Electricity averages **{avg_e:.1f}kg CO₂/day**. Solar could reduce this to near zero."})

    # vs regional average
    user_avg = df["total_co2"].mean()
    reg_avg = cfg["avg_daily_co2"]
    diff = user_avg - reg_avg
    if diff < 0:
        insights.append({"type": "good", "icon": "🌍",
                          "text": f"You're **{abs(diff):.1f}kg/day below** the {region} average ({reg_avg}kg). That's {abs(diff)*365:.0f}kg/year better than average!"})
    else:
        insights.append({"type": "warn", "icon": "🌍",
                          "text": f"You're {diff:.1f}kg/day **above** the {region} average. Small habit changes can close this gap quickly."})

    # Streak
    streak_days = len(df)
    if streak_days >= 7:
        insights.append({"type": "good", "icon": "🔥",
                          "text": f"You've logged **{streak_days} entries** — consistency is the key to real change. Keep the habit going!"})

    return insights[:6]

# ─── AI Assistant (Gemini / OpenAI / Built-in Fallback) ───────────────────────
def call_gemini(api_key, messages, user_context=""):
    """Call Google Gemini API"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # Build conversation history for Gemini
    contents = []
    system_prompt = f"""You are EcoBot, an expert AI assistant for EcoTrack — a carbon footprint tracking platform.
You have deep knowledge of climate science, carbon emissions, sustainability, and environmental policy.
Be concise, data-driven, and actionable. Use emojis sparingly for readability.
Always provide specific numbers and comparisons where possible.
{f"User context: {user_context}" if user_context else ""}
Keep responses under 300 words unless a detailed explanation is requested."""

    # First turn carries system context
    if messages:
        for i, msg in enumerate(messages):
            role = "user" if msg["role"] == "user" else "model"
            text = msg["content"]
            if i == 0 and role == "user":
                text = system_prompt + "\n\nUser: " + text
            contents.append({"role": role, "parts": [{"text": text}]})

    payload = json.dumps({"contents": contents, "generationConfig": {"maxOutputTokens": 500, "temperature": 0.7}})
    req = urllib.request.Request(url, data=payload.encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return None

def call_openai(api_key, messages, user_context=""):
    """Call OpenAI ChatGPT API"""
    url = "https://api.openai.com/v1/chat/completions"
    system_msg = f"""You are EcoBot, an expert AI sustainability assistant for EcoTrack.
You have deep knowledge of climate science, carbon footprints, and eco-friendly living.
Be concise, specific, and actionable. Use real data and numbers.
{f"User context: {user_context}" if user_context else ""}"""
    
    oai_messages = [{"role": "system", "content": system_msg}]
    for m in messages:
        oai_messages.append({"role": m["role"], "content": m["content"]})

    payload = json.dumps({"model": "gpt-3.5-turbo", "messages": oai_messages, "max_tokens": 500, "temperature": 0.7})
    req = urllib.request.Request(url, data=payload.encode(),
                                  headers={"Content-Type": "application/json",
                                           "Authorization": f"Bearer {api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
    except Exception:
        return None

def get_ai_response(question, chat_history, user_context, settings):
    """Route to best available AI, fallback to built-in"""
    messages = [{"role": r, "content": c} for r, c in chat_history]
    messages.append({"role": "user", "content": question})

    # Try Gemini first
    if settings.get("gemini"):
        resp = call_gemini(settings["gemini"], messages, user_context)
        if resp:
            return resp, "gemini"

    # Try OpenAI
    if settings.get("openai"):
        resp = call_openai(settings["openai"], messages, user_context)
        if resp:
            return resp, "openai"

    # Built-in knowledge base fallback
    return builtin_ai_response(question, user_context), "builtin"

def builtin_ai_response(question, user_context=""):
    """Comprehensive built-in AI with rich knowledge base"""
    q = question.lower()

    kb = {
        ("reduce carbon", "lower my footprint", "cut emissions", "save co2", "be greener"):
        """**How to Reduce Your Carbon Footprint — Top Actions by Impact:**

🚗 **Transport (biggest lever):** Switch to public transit, EV, or cycling. A petrol car emits ~0.21 kg CO₂/km; a bus emits ~0.09 kg. For flights, trains emit 96% less CO₂ than flying the same route.

⚡ **Home Energy:** Install solar panels — they eliminate grid emissions entirely. LED bulbs use 75% less energy. Smart thermostats save 10–15% on heating/cooling.

🥗 **Diet:** Shifting from meat-daily to flexitarian saves ~900 kg CO₂/year — equivalent to not driving for 3 months. Vegan diets have the lowest footprint.

🛍️ **Shopping:** Extend smartphone life by 2 years → saves ~80 kg CO₂. Buy secondhand clothing → 80% lower fashion footprint.

🌳 **Offset:** Plant trees, support Gold Standard carbon credits, or invest in community solar.

The average Indian emits ~11.5 kg/day; the 1.5°C-compatible target is ~5.5 kg/day.""",

        ("climate change", "global warming", "greenhouse gas", "paris agreement", "ipcc"):
        """**Climate Change — What You Need to Know:**

🌡️ Earth has warmed **+1.2°C** since pre-industrial times. At current rates, we're heading for 2.4–2.7°C by 2100.

**The science:** CO₂ from burning fossil fuels traps heat. Atmospheric CO₂ is now 421 ppm — highest in 3 million years.

**Key impacts already happening:**
- Sea level rise: +3.6mm/year (threatens 1 billion coastal people)
- Extreme weather: 5× more frequent heat extremes
- Biodiversity: 1 million species at risk
- Food security: 10% decline in crop yields per 1°C of warming

**The Paris Agreement** (195 countries) commits to limiting warming to 1.5°C. This requires cutting emissions 45% by 2030 and reaching net zero by 2050.

**Good news:** Renewables are now the cheapest electricity source in history. EV sales doubled in 2023. The solutions exist — deployment speed is the challenge.""",

        ("solar", "renewable energy", "wind power", "clean energy"):
        """**Renewable Energy — The Fast Facts:**

☀️ **Solar PV:** Costs fell 89% since 2010. Now the cheapest electricity ever produced. A 5 kW rooftop system in India generates ~7,000 kWh/year, saving ~5.7 tonnes CO₂.

🌬️ **Wind:** Onshore wind is now cheaper than coal. Offshore wind capacity is doubling every 4 years.

**Global capacity (2023):** 3,400 GW renewable — but we need 11,000 GW by 2030 for 1.5°C.

**In India:** PM Surya Ghar Yojana offers subsidies up to ₹78,000 for rooftop solar. Target: 500 GW renewable by 2030.

**Payback period for solar:** 5–7 years in India, 8–10 years in UK — then free electricity for 20+ more years.""",

        ("electric vehicle", "ev", "electric car", "tesla"):
        """**Electric Vehicles — Are They Really Green?**

⚡ **Lifecycle emissions:** EVs produce **50–70% less CO₂** than petrol cars over their lifetime, even accounting for battery manufacturing.

**Key factors:**
- In India (coal-heavy grid): EVs emit ~0.033 kg CO₂/km vs ~0.21 kg for petrol
- In UK (cleaner grid): EVs emit ~0.04 kg CO₂/km vs ~0.17 kg for petrol
- With solar charging: near-zero operational emissions

**Battery production:** A 75 kWh battery pack produces ~6–8 tonnes CO₂ to manufacture — but this is offset after ~25,000–50,000 km of driving.

**Bottom line:** Buy an EV + green energy tariff = single biggest personal transport action. Pair with rooftop solar = emissions near zero.""",

        ("food", "diet", "meat", "vegan", "vegetarian"):
        """**Food & Carbon — What You Eat Matters:**

🥩 **Animal products dominate food emissions:**
- Beef: 27 kg CO₂ per kg (highest)
- Lamb: 24 kg CO₂/kg
- Chicken: 6.9 kg CO₂/kg
- Tofu: 2.0 kg CO₂/kg
- Lentils: 0.9 kg CO₂/kg

**Annual diet footprints:**
- Vegan: ~0.5 tonnes CO₂/year
- Vegetarian: ~1.0 tonnes/year
- Average meat-eater: ~2.5 tonnes/year
- Heavy meat-eater: ~3.3 tonnes/year

**Agriculture drives 26% of global emissions** (livestock: 14.5%).

**Practical steps:** Meatless Monday saves ~330 kg CO₂/year. Buying local and seasonal reduces transport emissions by 10–15%.""",

        ("plastic", "waste", "recycling", "circular economy"):
        """**Plastic & Waste — The Hidden Footprint:**

🧴 **Plastic production:** Each kg of plastic releases ~6 kg CO₂. Global plastic production: 400 million tonnes/year = 2.4 billion tonnes CO₂.

**What you can do:**
- Reusable bags/bottles: saves 100–200 kg CO₂/year
- Composting food waste: cuts landfill methane (21× more potent than CO₂)
- Recycling properly: aluminium recycling saves 95% of the energy vs. virgin production

**Circular economy:** Designing products for reuse/repair cuts industrial emissions by 39%.

**India context:** Only 30% of plastic waste is recycled. Extended Producer Responsibility rules (2022) are shifting this.""",

        ("water", "water footprint", "water usage"):
        """**Water & Carbon — The Connection:**

💧 **Water treatment and heating** account for ~8% of global energy use.

**Your water footprint:**
- A 10-minute shower: ~60 litres, ~0.3 kg CO₂ (heated water)
- A bath: ~150 litres, ~0.7 kg CO₂
- Dishwasher vs hand washing: dishwasher uses 50% less water if full

**Virtual water in food:**
- 1 kg beef: 15,400 litres of water
- 1 kg wheat: 1,600 litres
- 1 cup coffee: 140 litres

**Simple wins:** Fix a dripping tap (saves 5,000 litres/year), use a water-efficient showerhead, collect rainwater for gardens.""",

        ("deforestation", "forest", "trees", "amazon"):
        """**Forests & Climate — Earth's Carbon Lungs:**

🌳 Forests store **861 billion tonnes of carbon** — twice what's in the atmosphere.

**The crisis:**
- 10 million hectares deforested annually (area of Iceland)
- Amazon: lost 17% of forest in 50 years, approaching 20–25% tipping point
- Deforestation: 10% of annual global emissions

**Reforestation potential:** Restoring 900 million hectares could absorb 205 billion tonnes CO₂.

**One tree absorbs:** ~22 kg CO₂/year (mature tree). To offset 1 tonne, you'd need ~45 trees over their lifetime.

**What you can do:** Support Grow-Trees.com, WeForest, or verified carbon offset projects. Avoid products linked to deforestation (palm oil, beef, soy).""",
    }

    for keywords, response in kb.items():
        if any(k in q for k in keywords):
            return response

    # Generic environmental response
    return f"""**EcoBot — Built-in Knowledge Base** 🌿

I can answer questions about:
- 🌡️ Climate change, Paris Agreement, IPCC findings
- ⚡ Renewable energy (solar, wind, hydro)
- 🚗 Transport emissions (EVs, public transit, aviation)
- 🥗 Food systems and dietary choices
- 🛍️ Sustainable shopping and circular economy
- ♻️ Waste, plastic, and recycling
- 💧 Water footprint and conservation
- 🌳 Forests, deforestation, and reforestation

**For smarter, context-aware answers:** Add your Gemini or OpenAI API key in ⚙️ Settings — I'll use real AI to answer any question with full conversational memory.

Try asking: *"How can I reduce my transport emissions?"* or *"What are the health benefits of a plant-based diet?"*

{f"Your context: {user_context}" if user_context else ""}"""

# ─── News Feed (RSS + NewsAPI) ─────────────────────────────────────────────────
@st.cache_data(ttl=1800)  # 30 min cache
def fetch_news(newsapi_key=""):
    articles = []

    # RSS feeds (no API key needed)
    rss_sources = [
        ("https://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "BBC Environment"),
        ("https://www.theguardian.com/environment/climate-crisis/rss", "The Guardian"),
        ("https://rss.nytimes.com/services/xml/rss/nyt/Climate.xml", "New York Times"),
    ]

    for url, source in rss_sources:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "EcoTrack/3.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                tree = ET.parse(resp)
                root = tree.getroot()
                ns = ""
                items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
                for item in items[:4]:
                    title_el = item.find("title")
                    link_el  = item.find("link")
                    desc_el  = item.find("description") or item.find("summary")
                    pub_el   = item.find("pubDate") or item.find("published")
                    title = title_el.text if title_el is not None else ""
                    link  = link_el.text if link_el is not None else "#"
                    desc  = desc_el.text if desc_el is not None else ""
                    pub   = pub_el.text[:16] if pub_el is not None and pub_el.text else ""
                    # Filter for climate/env keywords
                    combined = (title + desc).lower()
                    if any(k in combined for k in ["climate", "carbon", "emission", "renewable",
                                                    "solar", "fossil", "warming", "sustainability",
                                                    "environment", "green", "net zero", "biodiversity"]):
                        # Strip HTML from description
                        if desc:
                            import re
                            desc = re.sub(r'<[^>]+>', '', desc)[:200]
                        articles.append({
                            "title": title, "link": link,
                            "summary": desc.strip(), "source": source,
                            "date": pub,
                        })
        except Exception:
            pass

    # NewsAPI (optional, if key provided)
    if newsapi_key:
        try:
            url = (f"https://newsapi.org/v2/everything?"
                   f"q=climate+change+carbon+renewable+energy&"
                   f"sortBy=publishedAt&pageSize=6&language=en&"
                   f"apiKey={newsapi_key}")
            with urllib.request.urlopen(url, timeout=8) as resp:
                data = json.loads(resp.read())
                for a in data.get("articles", []):
                    if a.get("title") and a.get("url"):
                        articles.append({
                            "title": a["title"],
                            "link": a["url"],
                            "summary": (a.get("description") or "")[:200],
                            "source": a.get("source", {}).get("name", "NewsAPI"),
                            "date": (a.get("publishedAt") or "")[:10],
                        })
        except Exception:
            pass

    # Deduplicate by title
    seen = set()
    unique = []
    for a in articles:
        if a["title"] not in seen and a["title"]:
            seen.add(a["title"])
            unique.append(a)

    return unique[:12]

# ─── CSS Styling ───────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cabinet+Grotesk:wght@300;400;500;700;800&family=Fraunces:ital,opsz,wght@0,9..144,700;0,9..144,900;1,9..144,400&display=swap');

    html, body, [class*="css"] { font-family: 'Cabinet Grotesk', sans-serif !important; }
    .main, .stApp { background: #f4f8f5 !important; }
    .block-container { padding: 1.5rem 2rem !important; max-width: 1280px; }

    @media (max-width: 768px) {
        .block-container { padding: 0.8rem !important; }
        .hero-title { font-size: 1.6rem !important; }
        .hero-banner { padding: 1.2rem 1.5rem !important; }
        .eco-card { padding: 0.9rem !important; }
        .stat-number { font-size: 1.4rem !important; }
        [data-testid="column"] { min-width: 100% !important; }
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg,#062014 0%,#0d3b2e 50%,#062014 100%) !important;
        border-right: none !important;
    }
    [data-testid="stSidebar"] * { color: #a8d8b8 !important; }
    [data-testid="stSidebar"] .stButton > button {
        background: transparent !important; color: #a8d8b8 !important;
        border: 1px solid rgba(168,216,184,0.2) !important; border-radius: 8px !important;
        padding: 0.4rem 0.9rem !important; font-size: 0.86rem !important;
        font-weight: 500 !important; box-shadow: none !important;
        transition: all 0.18s !important; width: 100%;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,0.09) !important; color: #fff !important;
        border-color: rgba(255,255,255,0.3) !important; transform: none !important;
    }

    /* Hero */
    .hero-banner {
        background: linear-gradient(135deg,#0d3b2e 0%,#1a7a4a 55%,#2ecc71 100%);
        padding: 2.2rem 2.8rem; border-radius: 20px; margin-bottom: 1.5rem;
        position: relative; overflow: hidden;
        box-shadow: 0 8px 32px rgba(13,59,46,0.18);
    }
    .hero-banner::before {
        content:''; position:absolute; top:-80px; right:-80px;
        width:350px; height:350px;
        background:radial-gradient(circle,rgba(255,255,255,0.07) 0%,transparent 70%);
        border-radius:50%;
    }
    .hero-title {
        font-family:'Fraunces',serif !important; font-size:2.4rem !important;
        color:#fff !important; margin:0 0 0.3rem; line-height:1.15; font-weight:900;
    }
    .hero-sub { font-size:0.95rem; color:rgba(255,255,255,0.75); line-height:1.6; }

    /* Cards */
    .eco-card {
        background:#fff; border-radius:16px; padding:1.3rem;
        border:1px solid #e2f0e8; box-shadow:0 2px 12px rgba(13,59,46,0.05);
        transition:transform 0.2s,box-shadow 0.2s; height:100%;
    }
    .eco-card:hover { transform:translateY(-2px); box-shadow:0 8px 24px rgba(13,59,46,0.11); }
    .card-title { font-size:0.75rem; font-weight:700; color:#1a7a4a;
                  text-transform:uppercase; letter-spacing:0.06em; margin-bottom:0.2rem; }
    .card-value { font-family:'Fraunces',serif; font-size:2rem; color:#0d3b2e;
                  font-weight:700; line-height:1; }
    .card-unit { font-size:0.75rem; color:#7aab8a; margin-top:0.15rem; }

    /* Stats */
    .stat-row { display:flex; gap:0.7rem; flex-wrap:wrap; margin-bottom:1.2rem; }
    .stat-box {
        background:#fff; border-radius:12px; padding:1rem 1.2rem;
        flex:1; min-width:140px; border:1px solid #e2f0e8;
        border-left:3px solid #22c55e; box-shadow:0 1px 6px rgba(13,59,46,0.05);
    }
    .stat-label { font-size:0.7rem; text-transform:uppercase; letter-spacing:0.06em;
                  color:#7aab8a; font-weight:700; }
    .stat-number { font-size:1.6rem; font-weight:800; color:#0d3b2e; line-height:1.1; }

    /* Section Title */
    .section-title {
        font-family:'Fraunces',serif; font-size:1.25rem; color:#0d3b2e;
        margin:1.3rem 0 0.7rem; font-weight:700;
        border-bottom:2px solid #e2f0e8; padding-bottom:0.35rem;
    }

    /* Tips */
    .tip-box {
        background:#f0fdf4; border-left:3px solid #22c55e;
        border-radius:0 10px 10px 0; padding:0.75rem 1rem;
        margin:0.35rem 0; font-size:0.88rem; color:#14532d; line-height:1.5;
    }

    /* Insights */
    .insight-good { background:#f0fdf4; border-left:3px solid #22c55e;
                    border-radius:0 10px 10px 0; padding:0.7rem 1rem; margin:0.3rem 0;
                    font-size:0.88rem; color:#14532d; }
    .insight-warn { background:#fef9c3; border-left:3px solid #eab308;
                    border-radius:0 10px 10px 0; padding:0.7rem 1rem; margin:0.3rem 0;
                    font-size:0.88rem; color:#713f12; }
    .insight-action { background:#eff6ff; border-left:3px solid #3b82f6;
                      border-radius:0 10px 10px 0; padding:0.7rem 1rem; margin:0.3rem 0;
                      font-size:0.88rem; color:#1e3a5f; }
    .insight-info { background:#f8fafc; border-left:3px solid #94a3b8;
                    border-radius:0 10px 10px 0; padding:0.7rem 1rem; margin:0.3rem 0;
                    font-size:0.88rem; color:#475569; }

    /* Badges */
    .badge-pill {
        display:inline-flex; align-items:center; gap:0.3rem;
        background:#f0fdf4; color:#166534; border:1px solid #bbf7d0;
        border-radius:100px; padding:0.3rem 0.75rem;
        font-size:0.8rem; font-weight:700; margin:0.2rem;
    }
    .badge-locked { background:#f8fafc; color:#94a3b8; border-color:#e2e8f0; }

    /* Leaderboard */
    .lb-row {
        display:flex; align-items:center; background:#fff;
        border:1px solid #e2f0e8; border-radius:12px;
        padding:0.8rem 1.1rem; margin:0.35rem 0; gap:0.9rem;
        box-shadow:0 1px 5px rgba(13,59,46,0.04);
        transition:box-shadow 0.18s;
    }
    .lb-row:hover { box-shadow:0 4px 16px rgba(13,59,46,0.1); }
    .lb-rank { font-family:'Fraunces',serif; font-size:1.3rem; font-weight:900;
               width:36px; text-align:center; color:#7aab8a; }
    .lb-rank.gold { color:#d97706; } .lb-rank.silver { color:#64748b; } .lb-rank.bronze { color:#92400e; }
    .lb-username { font-weight:700; color:#0d3b2e; flex:1; font-size:0.92rem; }
    .lb-sub { font-size:0.74rem; color:#7aab8a; }
    .lb-co2 { font-family:'Fraunces',serif; font-size:1.2rem; font-weight:700; color:#16a34a; }
    .lb-badge { font-size:0.72rem; font-weight:700; padding:0.18rem 0.55rem;
                border-radius:100px; border:1px solid; }
    .bg-gold  { color:#d97706; border-color:#d97706; background:#fffbeb; }
    .bg-silver{ color:#64748b; border-color:#64748b; background:#f8fafc; }
    .bg-bronze{ color:#92400e; border-color:#92400e; background:#fef3c7; }
    .bg-green { color:#16a34a; border-color:#16a34a; background:#f0fdf4; }

    /* Chat */
    .chat-user {
        background:#0d3b2e; color:#fff; padding:0.7rem 1rem;
        border-radius:16px 16px 4px 16px; margin:0.4rem 0;
        max-width:78%; margin-left:auto; font-size:0.88rem;
    }
    .chat-bot {
        background:#fff; color:#1a3020; padding:0.7rem 1rem;
        border-radius:16px 16px 16px 4px; margin:0.4rem 0;
        max-width:84%; border:1px solid #e2f0e8;
        font-size:0.88rem; box-shadow:0 2px 8px rgba(13,59,46,0.06);
    }
    .chat-label { font-size:0.68rem; font-weight:700; text-transform:uppercase;
                  letter-spacing:0.07em; margin-bottom:0.2rem; }
    .ai-source { display:inline-flex; align-items:center; gap:0.3rem;
                 font-size:0.68rem; color:#7aab8a; margin-top:0.3rem; }

    /* News */
    .news-card {
        background:#fff; border-radius:14px; padding:1.1rem 1.3rem;
        border:1px solid #e2f0e8; margin-bottom:0.7rem;
        box-shadow:0 1px 6px rgba(13,59,46,0.04);
        transition:box-shadow 0.18s;
    }
    .news-card:hover { box-shadow:0 4px 16px rgba(13,59,46,0.1); }
    .news-source { font-size:0.7rem; font-weight:700; color:#1a7a4a;
                   text-transform:uppercase; letter-spacing:0.05em; }
    .news-title { font-size:0.93rem; font-weight:700; color:#0d3b2e;
                  margin:0.3rem 0; line-height:1.4; }
    .news-summary { font-size:0.82rem; color:#5a7a6a; line-height:1.5; }
    .news-date { font-size:0.72rem; color:#7aab8a; margin-top:0.3rem; }

    /* Region badge */
    .region-badge {
        display:inline-flex; align-items:center; gap:0.3rem;
        background:rgba(255,255,255,0.2); color:#fff;
        border:1px solid rgba(255,255,255,0.35); border-radius:100px;
        padding:0.22rem 0.75rem; font-size:0.76rem; font-weight:700;
    }

    /* Compare bar */
    .cbar-bg { height:7px; background:#e2f0e8; border-radius:100px; overflow:hidden; margin-top:0.25rem; }
    .cbar-fill { height:100%; border-radius:100px;
                 background:linear-gradient(90deg,#16a34a,#4ade80); }

    /* Buttons */
    .stButton > button {
        background:linear-gradient(135deg,#166534,#22c55e) !important;
        color:#fff !important; border:none !important; border-radius:10px !important;
        padding:0.5rem 1.5rem !important; font-weight:700 !important;
        font-size:0.86rem !important; transition:all 0.18s !important;
        box-shadow:0 3px 10px rgba(34,197,94,0.28) !important;
    }
    .stButton > button:hover {
        transform:translateY(-1px) !important;
        box-shadow:0 6px 16px rgba(34,197,94,0.38) !important;
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea textarea {
        background:#fff !important; color:#0d3b2e !important;
        border:1px solid #c8e6d0 !important; border-radius:10px !important;
    }
    .stSelectbox > div > div { border:1px solid #c8e6d0 !important; border-radius:10px !important; }
    .stMarkdown p, .stMarkdown li { color:#2d4a38 !important; }
    h1,h2,h3 { color:#0d3b2e !important; }
    .stAlert { border-radius:12px !important; }
    .stDataFrame { border-radius:12px !important; overflow:hidden; }
    </style>
    """, unsafe_allow_html=True)

# ─── PAGE: Home ────────────────────────────────────────────────────────────────
def page_home():
    st.markdown("""
    <div class="hero-banner">
        <div style="display:flex;align-items:center;gap:0.8rem;margin-bottom:0.7rem;">
            <span style="font-size:2.2rem;">🌿</span>
            <span class="hero-title">EcoTrack</span>
        </div>
        <div style="font-family:'Fraunces',serif;font-size:1.2rem;color:rgba(255,255,255,0.75);margin-bottom:0.5rem;font-style:italic;">
            Intelligent Carbon Footprint Tracker — v3.0
        </div>
        <div class="hero-sub">
            AI-powered insights · Real-time news · Daily tracking · Global leaderboard<br>
            Know your footprint. Shrink it. Make a real difference.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="stat-row">
        <div class="stat-box" style="border-left-color:#ef4444;">
            <div class="stat-label">Global CO₂ (2023)</div>
            <div class="stat-number" style="color:#dc2626;">37.4B</div>
            <div class="card-unit">tonnes emitted</div>
        </div>
        <div class="stat-box" style="border-left-color:#f97316;">
            <div class="stat-label">Avg per Person</div>
            <div class="stat-number" style="color:#ea580c;">12.9kg</div>
            <div class="card-unit">CO₂ per day</div>
        </div>
        <div class="stat-box" style="border-left-color:#22c55e;">
            <div class="stat-label">Safe Target</div>
            <div class="stat-number" style="color:#16a34a;">5.5kg</div>
            <div class="card-unit">CO₂/day (1.5°C)</div>
        </div>
        <div class="stat-box" style="border-left-color:#3b82f6;">
            <div class="stat-label">Warming So Far</div>
            <div class="stat-number" style="color:#2563eb;">+1.2°C</div>
            <div class="card-unit">above pre-industrial</div>
        </div>
        <div class="stat-box" style="border-left-color:#a855f7;">
            <div class="stat-label">Net Zero Target</div>
            <div class="stat-number" style="color:#9333ea;">2050</div>
            <div class="card-unit">Paris Agreement goal</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">⚡ Why EcoTrack?</div>', unsafe_allow_html=True)
    features = [
        ("🧮", "Smart Calculator", "Region-aware emissions across 6 categories with real data from IEA, EPA, CEA."),
        ("🤖", "AI Assistant", "Gemini/GPT-4 powered advisor with your carbon data as context. Any question answered."),
        ("📈", "Daily Tracking", "Build habits with streaks, badges, and week-over-week progress insights."),
        ("🌐", "Live News Feed", "Climate headlines from BBC, Guardian, NYT updated every 30 minutes."),
        ("🏆", "Leaderboard", "Compete globally. Lowest average emissions wins. Gamified badges."),
        ("📊", "Impact Reports", "Deep-dive analysis comparing you to India, global, and sustainable averages."),
    ]
    cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(features):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="eco-card" style="margin-bottom:0.8rem;">
                <div style="font-size:1.8rem;margin-bottom:0.4rem;">{icon}</div>
                <div class="card-title">{title}</div>
                <p style="color:#5a7a6a;font-size:0.85rem;line-height:1.55;margin:0;">{desc}</p>
            </div>""", unsafe_allow_html=True)

    if not st.session_state.get("logged_in"):
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, _, _ = st.columns(4)
        with c1:
            if st.button("🚀 Get Started Free", use_container_width=True):
                st.session_state.page = "Signup"; st.rerun()
        with c2:
            if st.button("🔑 Login", use_container_width=True):
                st.session_state.page = "Login"; st.rerun()

# ─── PAGE: Signup ──────────────────────────────────────────────────────────────
def page_signup():
    _, c2, _ = st.columns([1,2,1])
    with c2:
        st.markdown("""
        <div style="text-align:center;margin-bottom:1.5rem;">
            <div style="font-size:2.5rem;">🌱</div>
            <div class="hero-title" style="font-size:1.8rem;color:#0d3b2e;">Create Your Account</div>
            <div style="color:#7aab8a;margin-top:0.4rem;font-size:0.88rem;">
                Join EcoTrack and start measuring your impact
            </div>
        </div>""", unsafe_allow_html=True)
        with st.form("signup_form"):
            username = st.text_input("👤 Username")
            email    = st.text_input("📧 Email")
            region   = st.selectbox("🌍 Your Region", list(REGION_CONFIG.keys()))
            pwd      = st.text_input("🔒 Password", type="password", placeholder="Min 8 characters")
            pwd2     = st.text_input("🔒 Confirm Password", type="password")
            if st.form_submit_button("Create Account 🌿", use_container_width=True):
                if not all([username, email, pwd, pwd2]):
                    st.error("Fill in all fields.")
                elif len(pwd) < 8:
                    st.error("Password must be 8+ characters.")
                elif pwd != pwd2:
                    st.error("Passwords don't match.")
                else:
                    ok, msg = create_user(username, email, pwd, region)
                    if ok:
                        st.success(f"✅ {msg} Please log in.")
                        st.session_state.page = "Login"; st.rerun()
                    else:
                        st.error(f"❌ {msg}")
        if st.button("Already have an account? Login →", use_container_width=True):
            st.session_state.page = "Login"; st.rerun()

# ─── PAGE: Login ───────────────────────────────────────────────────────────────
def page_login():
    _, c2, _ = st.columns([1,2,1])
    with c2:
        st.markdown("""
        <div style="text-align:center;margin-bottom:1.5rem;">
            <div style="font-size:2.5rem;">🔑</div>
            <div class="hero-title" style="font-size:1.8rem;color:#0d3b2e;">Welcome Back</div>
        </div>""", unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("👤 Username")
            pwd      = st.text_input("🔒 Password", type="password")
            if st.form_submit_button("Login 🌿", use_container_width=True):
                if username and pwd:
                    user = authenticate_user(username, pwd)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_id   = user[0]
                        st.session_state.username  = user[1]
                        st.session_state.region    = user[2] or "India"
                        st.success(f"✅ Welcome, {user[1]}!")
                        st.session_state.page = "Dashboard"; st.rerun()
                    else:
                        st.error("❌ Invalid credentials.")
                else:
                    st.error("Enter username and password.")
        if st.button("New here? Create an account →", use_container_width=True):
            st.session_state.page = "Signup"; st.rerun()

# ─── PAGE: Dashboard ──────────────────────────────────────────────────────────
def page_dashboard():
    if not st.session_state.get("logged_in"):
        st.warning("Please log in.")
        if st.button("Login"): st.session_state.page = "Login"; st.rerun()
        return

    uid    = st.session_state.user_id
    uname  = st.session_state.username
    region = st.session_state.get("region", "India")
    cfg    = REGION_CONFIG[region]
    df     = get_logs(uid)
    gami   = compute_gamification(df)

    st.markdown(f"""
    <div class="hero-banner" style="padding:1.8rem 2.5rem;">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.8rem;">
        <div style="display:flex;align-items:center;gap:0.9rem;">
          <div style="font-size:2.2rem;">🌿</div>
          <div>
            <div class="hero-title" style="font-size:1.55rem;">Good day, {uname}!</div>
            <div style="color:rgba(255,255,255,0.65);font-size:0.82rem;">
              {datetime.now().strftime("%A, %B %d %Y")}
            </div>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:0.4rem;">
          <div class="region-badge">{cfg['flag']} {region}</div>
          <div style="color:rgba(255,255,255,0.7);font-size:0.78rem;">
            {gami['level']} · {gami['points']} pts · 🔥 {gami['streak']}-day streak
          </div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    if df.empty:
        st.info("🌱 No data yet — log your first entry in **Carbon Calculator**.")
        c1, _ = st.columns([1, 3])
        with c1:
            if st.button("Open Calculator →"):
                st.session_state.page = "Carbon Calculator"; st.rerun()
        return

    total_co2  = df["total_co2"].sum()
    avg_co2    = df["total_co2"].mean()
    entries    = len(df)
    green_score= max(0, 100 - min(100, (avg_co2 / 60) * 100))
    reg_avg    = cfg["avg_daily_co2"]
    vs_pct     = ((avg_co2 - reg_avg) / reg_avg) * 100
    vs_col     = "#16a34a" if vs_pct < 0 else "#dc2626"
    vs_lbl     = f"{'↓' if vs_pct < 0 else '↑'} {abs(vs_pct):.0f}% vs {region} avg"

    c1, c2, c3, c4 = st.columns(4)
    kpis = [
        ("🌍", "Total CO₂", f"{total_co2:.1f}", "kg emitted"),
        ("📊", "Daily Avg", f"{avg_co2:.1f}", "kg CO₂/day"),
        ("📝", "Entries", str(entries), "days logged"),
        ("🏆", "Green Score", f"{green_score:.0f}", "/ 100"),
    ]
    for col, (icon, title, val, unit) in zip([c1,c2,c3,c4], kpis):
        with col:
            extra = f'<div style="font-size:0.72rem;color:{vs_col};font-weight:700;margin-top:0.2rem;">{vs_lbl}</div>' \
                    if title == "Daily Avg" else ""
            st.markdown(f"""
            <div class="eco-card" style="text-align:center;">
              <div style="font-size:1.7rem;">{icon}</div>
              <div class="card-title">{title}</div>
              <div class="card-value">{val}</div>
              <div class="card-unit">{unit}</div>
              {extra}
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Trend chart + breakdown
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown('<div class="section-title">📈 Emission Trend</div>', unsafe_allow_html=True)
        dfs = df.sort_values("log_date").copy()
        dfs["log_date"] = pd.to_datetime(dfs["log_date"])
        dfs["rolling7"] = dfs["total_co2"].rolling(7, min_periods=1).mean()
        fig = go.Figure()
        fig.add_trace(go.Bar(x=dfs["log_date"], y=dfs["total_co2"],
                             marker_color="rgba(34,197,94,0.35)", name="Daily", showlegend=True))
        fig.add_trace(go.Scatter(x=dfs["log_date"], y=dfs["rolling7"],
                                 mode="lines", line=dict(color="#166534", width=2.5),
                                 name="7-day avg"))
        fig.add_hline(y=reg_avg, line_dash="dot", line_color="#dc2626",
                      annotation_text=f"{region} avg", annotation_font_color="#dc2626",
                      annotation_font_size=10)
        fig.add_hline(y=5.5, line_dash="dot", line_color="#16a34a",
                      annotation_text="Target", annotation_font_color="#16a34a",
                      annotation_font_size=10)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          margin=dict(l=0,r=0,t=10,b=0), height=240,
                          xaxis=dict(showgrid=False, color="#7aab8a"),
                          yaxis=dict(showgrid=True, gridcolor="#e2f0e8", color="#7aab8a", title="kg CO₂"),
                          font=dict(family="Cabinet Grotesk"),
                          legend=dict(font=dict(color="#5a7a6a", size=10)))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<div class="section-title">🥧 Emission Sources</div>', unsafe_allow_html=True)
        src = ["travel_co2","electricity_co2","food_co2","lifestyle_co2","flight_co2"]
        avail = [c for c in src if c in df.columns]
        labels = [c.replace("_co2","").title() for c in avail]
        vals   = [df[c].sum() for c in avail]
        fig2 = go.Figure(go.Pie(
            labels=labels, values=vals, hole=0.5,
            marker_colors=["#22c55e","#06b6d4","#f59e0b","#a855f7","#f87171"],
            textfont=dict(color="#0d3b2e", size=10)))
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                           margin=dict(l=0,r=0,t=10,b=0), height=240,
                           font=dict(family="Cabinet Grotesk", color="#5a7a6a"),
                           legend=dict(font=dict(size=10)))
        st.plotly_chart(fig2, use_container_width=True)

    # Smart Insights
    st.markdown('<div class="section-title">💡 Smart Insights</div>', unsafe_allow_html=True)
    insights = generate_insights(df, region)
    for ins in insights:
        css = f"insight-{ins['type']}"
        st.markdown(f'<div class="{css}">{ins["icon"]} {ins["text"]}</div>',
                    unsafe_allow_html=True)

    # Badges + Streak
    st.markdown('<div class="section-title">🏅 Your Achievements</div>', unsafe_allow_html=True)
    ba, bb = st.columns([2, 1])
    with ba:
        badge_html = ""
        for b in BADGES:
            earned = b in gami["badges"]
            cls = "badge-pill" if earned else "badge-pill badge-locked"
            badge_html += f'<span class="{cls}">{b["name"]}</span>'
        st.markdown(f'<div style="line-height:2.5;">{badge_html}</div>', unsafe_allow_html=True)
        if gami["next_badge"]:
            nb = gami["next_badge"]
            st.markdown(f'<div style="font-size:0.8rem;color:#7aab8a;margin-top:0.5rem;">Next: <b>{nb["name"]}</b> — {nb["desc"]}</div>',
                        unsafe_allow_html=True)
    with bb:
        st.markdown(f"""
        <div class="eco-card" style="text-align:center;">
          <div style="font-size:2rem;">🔥</div>
          <div class="card-title">Logging Streak</div>
          <div class="card-value">{gami['streak']}</div>
          <div class="card-unit">consecutive days</div>
          <div style="margin-top:0.5rem;font-size:0.8rem;color:#7aab8a;">{gami['level']}</div>
        </div>""", unsafe_allow_html=True)

    # Weekly comparison chart
    st.markdown('<div class="section-title">📅 Weekly Breakdown</div>', unsafe_allow_html=True)
    df_week = df.copy()
    df_week["log_date"] = pd.to_datetime(df_week["log_date"])
    df_week["week"] = df_week["log_date"].dt.strftime("W%V %Y")
    weekly = df_week.groupby("week")["total_co2"].mean().reset_index().tail(8)
    fig_w = go.Figure(go.Bar(x=weekly["week"], y=weekly["total_co2"],
                             marker_color="#22c55e", text=[f"{v:.1f}" for v in weekly["total_co2"]],
                             textposition="outside", textfont=dict(color="#1a7a4a", size=10)))
    fig_w.add_hline(y=reg_avg, line_dash="dot", line_color="#dc2626",
                    annotation_text=f"{region} avg ({reg_avg}kg)",
                    annotation_font_color="#dc2626", annotation_font_size=10)
    fig_w.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=0,r=0,t=10,b=0), height=220,
                        xaxis=dict(color="#7aab8a"), yaxis=dict(showgrid=True, gridcolor="#e2f0e8",
                        color="#7aab8a", title="Avg kg CO₂/day"),
                        font=dict(family="Cabinet Grotesk"))
    st.plotly_chart(fig_w, use_container_width=True)

    # Recent logs
    st.markdown('<div class="section-title">🗒️ Recent Activity</div>', unsafe_allow_html=True)
    show = ["log_date","transport_mode","food_type","electricity_source","total_co2","impact_score"]
    avail_show = [c for c in show if c in df.columns]
    disp = df[avail_show].head(7).copy()
    disp.columns = [c.replace("_"," ").title() for c in avail_show]
    st.dataframe(disp, use_container_width=True, hide_index=True)

# ─── PAGE: Carbon Calculator ──────────────────────────────────────────────────
def page_calculator():
    if not st.session_state.get("logged_in"):
        st.warning("Please log in."); return

    region = st.session_state.get("region", "India")
    cfg    = REGION_CONFIG[region]

    st.markdown(f"""
    <div class="hero-banner" style="padding:1.8rem 2.5rem;">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.8rem;">
        <div>
          <div class="hero-title" style="font-size:1.55rem;">🧮 Carbon Calculator</div>
          <div style="color:rgba(255,255,255,0.65);font-size:0.82rem;">
            6-category region-aware footprint engine
          </div>
        </div>
        <div class="region-badge">{cfg['flag']} {region} · {cfg['grid_label']}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    new_region = st.selectbox("🌍 Region", list(REGION_CONFIG.keys()),
                               index=list(REGION_CONFIG.keys()).index(region))
    if new_region != region:
        st.session_state.region = new_region; st.rerun()

    log_date = st.date_input("📅 Date to log", value=date.today(), max_value=date.today())

    cf, cr = st.columns([1,1], gap="large")
    with cf:
        st.markdown('<div class="section-title">🚗 Transport</div>', unsafe_allow_html=True)
        transport_mode = st.selectbox("Mode of Transport", list(TRANSPORT_MODES.keys()))
        travel_km = st.slider("Daily Travel Distance (km)", 0, 250, 20)
        mode = TRANSPORT_MODES.get(transport_mode, "car")
        em_map = {"car": cfg["car_factor"], "diesel": cfg["car_factor"]*1.05,
                  "ev": cfg["ev_kwh_per_km"]*cfg["electricity_factor"],
                  "bus": cfg["bus_factor"], "train": cfg["train_factor"],
                  "moto": cfg["moto_factor"], "zero": 0.0}
        ef = em_map.get(mode, cfg["car_factor"])
        st.caption(f"Emission factor: **{ef:.4f} kg CO₂/km** for {transport_mode} in {region}")

        st.markdown('<div class="section-title">⚡ Energy</div>', unsafe_allow_html=True)
        electricity_source = st.selectbox("Electricity Source", list(ELECTRICITY_SOURCES.keys()))
        electricity_units  = st.slider("Daily Electricity Use (kWh)", 0, 100, 12)
        eff_factor = cfg["electricity_factor"] * ELECTRICITY_SOURCES[electricity_source]
        st.caption(f"Effective factor: **{eff_factor:.3f} kg CO₂/kWh** ({electricity_source})")

        st.markdown('<div class="section-title">🌱 Food & Lifestyle</div>', unsafe_allow_html=True)
        food_type = st.selectbox("🥗 Diet", list(FOOD_EMISSIONS.keys()), index=1)
        plastic_level  = st.select_slider("🧴 Plastic Use", [1,2,3,4,5], value=2,
                                           format_func=lambda x:["Minimal","Low","Moderate","High","Excessive"][x-1])
        shopping_level = st.select_slider("🛍️ Shopping", [1,2,3,4,5], value=2,
                                           format_func=lambda x:["Minimal","Secondhand","Average","Frequent","Heavy"][x-1])
        water_usage    = st.select_slider("💧 Water Use (×avg)", [1,2,3,4,5], value=3,
                                           format_func=lambda x:["Very Low","Low","Average","High","Very High"][x-1])
        waste_bags     = st.select_slider("🗑️ Waste Bags/day", [0,1,2,3,4], value=1)

        st.markdown('<div class="section-title">✈️ Air Travel</div>', unsafe_allow_html=True)
        flights_per_year = st.slider("Flights per Year", 0, 40, 2)

        calc_btn = st.button("⚡ Calculate My Footprint", use_container_width=True)

    if calc_btn or "calc_result" in st.session_state:
        if calc_btn:
            total, score, tips, bd, vs_avg, reg_avg = calculate_carbon(
                region, travel_km, transport_mode, electricity_units,
                electricity_source, water_usage, waste_bags, plastic_level,
                food_type, shopping_level, flights_per_year)
            st.session_state.calc_result = dict(
                total=total, score=score, tips=tips, bd=bd,
                vs_avg=vs_avg, reg_avg=reg_avg, region=region,
                travel_km=travel_km, transport_mode=transport_mode,
                electricity_units=electricity_units, electricity_source=electricity_source,
                water_usage=water_usage, waste_bags=waste_bags,
                plastic_level=plastic_level, food_type=food_type,
                shopping_level=shopping_level, flights_per_year=flights_per_year,
                log_date=str(log_date))

        r = st.session_state.calc_result
        with cr:
            st.markdown('<div class="section-title">📊 Results</div>', unsafe_allow_html=True)
            col = "#16a34a" if r["total"] < 15 else "#d97706" if r["total"] < 30 else "#dc2626"
            lbl = "🟢 Low Impact" if r["total"] < 15 else "🟡 Moderate" if r["total"] < 30 else "🔴 High Impact"
            vs_c = "#16a34a" if r["vs_avg"] < 0 else "#dc2626"
            vs_s = f"{'↓' if r['vs_avg'] < 0 else '↑'} {abs(r['vs_avg']):.0f}% vs {r['region']} avg ({r['reg_avg']:.1f}kg)"

            st.markdown(f"""
            <div class="eco-card" style="text-align:center;margin-bottom:0.8rem;">
              <div style="font-size:0.72rem;color:#7aab8a;text-transform:uppercase;letter-spacing:0.08em;">
                Total Daily CO₂
              </div>
              <div style="font-family:'Fraunces',serif;font-size:3.5rem;color:{col};font-weight:900;line-height:1;">
                {r['total']:.1f}
              </div>
              <div style="font-size:0.9rem;color:#7aab8a;margin-bottom:0.3rem;">kg CO₂ / day</div>
              <div style="font-size:0.95rem;font-weight:700;color:{col};">{lbl}</div>
              <div style="font-size:0.78rem;color:{vs_c};margin-top:0.3rem;font-weight:700;">{vs_s}</div>
            </div>""", unsafe_allow_html=True)

            # Gauge
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number",
                value=r["score"],
                number={"font": {"color": "#0d3b2e", "family": "Fraunces", "size": 24}},
                title={"text": "Impact Score (0=best)", "font": {"size": 11, "color": "#7aab8a"}},
                gauge={
                    "axis": {"range": [0,100], "tickcolor":"#7aab8a",
                             "tickfont":{"color":"#7aab8a","size":9}},
                    "bar": {"color": col},
                    "bgcolor": "#f4f8f5", "bordercolor": "#e2f0e8",
                    "steps": [{"range":[0,33],"color":"#dcfce7"},
                               {"range":[33,66],"color":"#fef9c3"},
                               {"range":[66,100],"color":"#fee2e2"}],
                }))
            fig_g.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                                margin=dict(l=20,r=20,t=30,b=10), height=190,
                                font=dict(family="Cabinet Grotesk"))
            st.plotly_chart(fig_g, use_container_width=True)

            st.markdown('<div class="section-title">💡 Smart Tips</div>', unsafe_allow_html=True)
            for tip in r["tips"]:
                st.markdown(f'<div class="tip-box">{tip}</div>', unsafe_allow_html=True)

        # Breakdown bar
        st.markdown('<div class="section-title">🔍 Emission Breakdown</div>', unsafe_allow_html=True)
        ca, cb = st.columns(2)
        with ca:
            fig_b = go.Figure(go.Bar(
                x=list(r["bd"].keys()), y=list(r["bd"].values()),
                marker_color=["#22c55e","#06b6d4","#f59e0b","#a855f7","#f87171"],
                text=[f"{v:.2f}kg" for v in r["bd"].values()],
                textposition="outside", textfont=dict(color="#1a7a4a", size=10)))
            fig_b.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                margin=dict(l=0,r=0,t=10,b=0), height=250,
                                yaxis=dict(showgrid=True, gridcolor="#e2f0e8",
                                           title="kg CO₂", color="#7aab8a"),
                                xaxis=dict(color="#7aab8a"),
                                font=dict(family="Cabinet Grotesk"))
            st.plotly_chart(fig_b, use_container_width=True)

        with cb:
            # Benchmark comparison
            yearly = r["total"] * 365
            benchmarks = {"You":r["total"], f"{region}":r["reg_avg"], "Global":12.9, "Target":5.5}
            bm_cols = ["#22c55e","#06b6d4","#f59e0b","#16a34a"]
            fig_bm = go.Figure(go.Bar(
                x=list(benchmarks.keys()), y=list(benchmarks.values()),
                marker_color=bm_cols,
                text=[f"{v:.1f}" for v in benchmarks.values()],
                textposition="outside", textfont=dict(color="#1a7a4a", size=10)))
            fig_bm.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                 margin=dict(l=0,r=0,t=10,b=0), height=250,
                                 yaxis=dict(showgrid=True, gridcolor="#e2f0e8",
                                            title="kg CO₂/day", color="#7aab8a"),
                                 xaxis=dict(color="#7aab8a"),
                                 font=dict(family="Cabinet Grotesk"))
            st.plotly_chart(fig_bm, use_container_width=True)

        # Annual projection
        yearly = r["total"] * 365
        trees  = yearly / 22
        excess = yearly / 1000 - 2.0
        p1, p2, p3 = st.columns(3)
        for col_w, (ico, tit, val, unit, c) in zip([p1,p2,p3], [
            ("📆","Yearly Total",f"{yearly:.0f}","kg CO₂/year","#dc2626"),
            ("🌳","Trees Needed",f"{trees:.0f}","trees to offset","#16a34a"),
            ("🎯","vs 1.5°C Goal",f"{'↑' if excess>0 else '↓'}{abs(excess):.2f}t",
             "above/below 2t/yr","#d97706" if excess>0 else "#16a34a"),
        ]):
            with col_w:
                st.markdown(f"""
                <div class="eco-card" style="text-align:center;">
                  <div style="font-size:1.5rem;">{ico}</div>
                  <div class="card-title">{tit}</div>
                  <div class="card-value" style="color:{c};">{val}</div>
                  <div class="card-unit">{unit}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("💾 Save to My Log", use_container_width=True):
                save_log(st.session_state.user_id, r["region"], r["log_date"],
                         r["travel_km"], r["transport_mode"],
                         r["electricity_units"], r["electricity_source"],
                         r["water_usage"], r["waste_bags"], r["plastic_level"],
                         r["food_type"], r["shopping_level"], r["flights_per_year"],
                         r["total"], r["score"], r["bd"])
                st.success("✅ Saved! Head to Dashboard to see your trends.")
                del st.session_state.calc_result
                st.rerun()
        with col_s2:
            if st.button("🔄 Recalculate", use_container_width=True):
                if "calc_result" in st.session_state:
                    del st.session_state.calc_result
                st.rerun()

# ─── PAGE: AI Assistant ────────────────────────────────────────────────────────
def page_ai_assistant():
    uid    = st.session_state.get("user_id")
    region = st.session_state.get("region", "India")
    cfg    = REGION_CONFIG[region]

    st.markdown(f"""
    <div class="hero-banner" style="padding:1.8rem 2.5rem;">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.8rem;">
        <div>
          <div class="hero-title" style="font-size:1.55rem;">🤖 AI Environmental Assistant</div>
          <div style="color:rgba(255,255,255,0.65);font-size:0.82rem;">
            Gemini / GPT-4 powered · Context-aware · Conversational memory
          </div>
        </div>
        <div class="region-badge">{cfg['flag']} {region}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # API settings notice
    settings = get_user_settings(uid) if uid else {"gemini": "", "newsapi": "", "openai": ""}
    has_ai = settings.get("gemini") or settings.get("openai")

    if not has_ai:
        st.info("💡 **Tip:** Add your Gemini or OpenAI API key in ⚙️ Settings for full AI power. Currently using built-in knowledge base.")

    # Build user context from their data
    user_context = ""
    if uid:
        df = get_logs(uid)
        if not df.empty:
            avg = df["total_co2"].mean()
            entries = len(df)
            top_mode = df["transport_mode"].mode()[0] if "transport_mode" in df.columns and not df.empty else "unknown"
            top_food = df["food_type"].mode()[0] if "food_type" in df.columns and not df.empty else "unknown"
            user_context = (f"User is in {region}. Avg daily CO₂: {avg:.1f}kg ({entries} logs). "
                            f"Typical transport: {top_mode}. Diet: {top_food}. "
                            f"Regional avg: {REGION_CONFIG[region]['avg_daily_co2']}kg/day.")

    # Suggested questions
    suggested = [
        f"How can I reduce my carbon footprint in {region}?",
        "What is climate change and why does it matter?",
        "How do EVs compare to petrol cars in emissions?",
        f"What are the benefits of solar energy in {region}?",
        "How does my diet affect my carbon footprint?",
        "What is the Paris Agreement and its targets?",
    ]
    st.markdown('<div class="section-title">💬 Quick Questions</div>', unsafe_allow_html=True)
    cols_s = st.columns(3)
    for i, q in enumerate(suggested):
        with cols_s[i % 3]:
            if st.button(q[:45] + ("…" if len(q) > 45 else ""), key=f"sq_{i}", use_container_width=True):
                if uid:
                    history = get_ai_history(uid)
                    resp, src = get_ai_response(q, history, user_context, settings)
                    save_ai_message(uid, "user", q)
                    save_ai_message(uid, "assistant", resp)
                else:
                    st.session_state.setdefault("chat_history", [])
                    st.session_state.chat_history.append(("user", q))
                    resp, src = get_ai_response(q, st.session_state.chat_history, user_context, settings)
                    st.session_state.chat_history.append(("assistant", resp))
                st.rerun()

    # Chat history
    st.markdown('<div class="section-title">🗨️ Conversation</div>', unsafe_allow_html=True)
    if uid:
        history = get_ai_history(uid, 30)
    else:
        history = st.session_state.get("chat_history", [])

    if not history:
        st.markdown("""
        <div style="text-align:center;padding:2.5rem;color:#7aab8a;">
          <div style="font-size:2.5rem;margin-bottom:0.7rem;">🌱</div>
          <div style="font-size:0.95rem;">Ask anything about climate, energy, or sustainability!</div>
          <div style="font-size:0.8rem;margin-top:0.3rem;">Your conversation is saved and used as context for future questions.</div>
        </div>""", unsafe_allow_html=True)

    ai_source_icons = {"gemini": "✨ Gemini", "openai": "🤖 GPT", "builtin": "📚 Built-in"}
    for role, content in history:
        if role == "user":
            st.markdown(f"""
            <div style="display:flex;justify-content:flex-end;margin:0.4rem 0;">
              <div>
                <div class="chat-label" style="text-align:right;color:#7aab8a;">You</div>
                <div class="chat-user">{content}</div>
              </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display:flex;justify-content:flex-start;margin:0.4rem 0;">
              <div>
                <div class="chat-label" style="color:#1a7a4a;">🌿 EcoBot</div>
                <div class="chat-bot">{content}</div>
              </div>
            </div>""", unsafe_allow_html=True)

    # Input
    with st.form("chat_form", clear_on_submit=True):
        ca, cb = st.columns([5,1])
        with ca:
            user_input = st.text_input("", placeholder="Ask about climate change, solar energy, EVs, diet, carbon markets...",
                                        label_visibility="collapsed")
        with cb:
            send = st.form_submit_button("Send 🌿", use_container_width=True)

    if send and user_input.strip():
        if uid:
            history = get_ai_history(uid, 20)
            resp, src = get_ai_response(user_input, history, user_context, settings)
            save_ai_message(uid, "user", user_input)
            save_ai_message(uid, "assistant", resp)
        else:
            st.session_state.setdefault("chat_history", [])
            history = st.session_state.chat_history
            resp, src = get_ai_response(user_input, history, user_context, settings)
            st.session_state.chat_history.append(("user", user_input))
            st.session_state.chat_history.append(("assistant", resp))
        st.rerun()

    col_cl, col_exp = st.columns(2)
    with col_cl:
        if history and st.button("🗑️ Clear Conversation", use_container_width=True):
            if uid: clear_ai_history(uid)
            else: st.session_state.chat_history = []
            st.rerun()
    with col_exp:
        if user_context:
            with st.expander("🔍 My Context Used by AI"):
                st.caption(user_context)

# ─── PAGE: News Feed ──────────────────────────────────────────────────────────
def page_news():
    region = st.session_state.get("region", "India")
    uid    = st.session_state.get("user_id")
    settings = get_user_settings(uid) if uid else {"newsapi": ""}

    st.markdown("""
    <div class="hero-banner" style="padding:1.8rem 2.5rem;">
      <div class="hero-title" style="font-size:1.55rem;">🌐 Climate News Feed</div>
      <div style="color:rgba(255,255,255,0.65);font-size:0.82rem;">
        Live headlines from BBC, Guardian, NYT · Updated every 30 minutes
      </div>
    </div>""", unsafe_allow_html=True)

    with st.spinner("Fetching latest climate news…"):
        articles = fetch_news(settings.get("newsapi", ""))

    if not articles:
        st.info("📡 Could not fetch live news. Check your internet connection or add a NewsAPI key in Settings for more sources.")
        # Show placeholder cards
        placeholders = [
            ("Global Renewable Energy Capacity Hits Record 3,400 GW", "IEA reports unprecedented growth in solar and wind installations globally.", "IEA", "2024"),
            ("Scientists Warn Arctic Sea Ice at Lowest Ever Recorded", "New satellite data shows Arctic summer ice has shrunk to record levels.", "BBC Science", "2024"),
            ("India Surpasses 100 GW Solar Capacity Milestone", "India reaches a landmark in its renewable energy transition ahead of schedule.", "The Hindu", "2024"),
        ]
        for title, summary, source, date_s in placeholders:
            st.markdown(f"""
            <div class="news-card">
              <div class="news-source">📰 {source}</div>
              <div class="news-title">{title}</div>
              <div class="news-summary">{summary}</div>
              <div class="news-date">📅 {date_s} (placeholder)</div>
            </div>""", unsafe_allow_html=True)
        return

    st.markdown(f'<div class="section-title">📰 {len(articles)} Latest Stories</div>', unsafe_allow_html=True)
    
    # Filter controls
    sources = list({a["source"] for a in articles})
    col_f1, col_f2 = st.columns([2, 1])
    with col_f2:
        selected_source = st.selectbox("Filter by Source", ["All"] + sources)

    filtered = articles if selected_source == "All" else [a for a in articles if a["source"] == selected_source]

    for a in filtered:
        link_html = f'<a href="{a["link"]}" target="_blank" style="color:#16a34a;font-size:0.8rem;text-decoration:none;font-weight:700;">Read Full Article →</a>' if a.get("link") and a["link"] != "#" else ""
        st.markdown(f"""
        <div class="news-card">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div class="news-source">📰 {a['source']}</div>
            <div class="news-date">{a.get('date', '')}</div>
          </div>
          <div class="news-title">{a['title']}</div>
          <div class="news-summary">{a.get('summary', '')}</div>
          <div style="margin-top:0.5rem;">{link_html}</div>
        </div>""", unsafe_allow_html=True)

    st.caption("💡 Add a NewsAPI key in ⚙️ Settings to include additional sources and more articles.")

# ─── PAGE: Leaderboard ────────────────────────────────────────────────────────
def page_leaderboard():
    st.markdown("""
    <div class="hero-banner" style="padding:1.8rem 2.5rem;">
      <div class="hero-title" style="font-size:1.55rem;">🏆 Global Leaderboard</div>
      <div style="color:rgba(255,255,255,0.65);font-size:0.82rem;">
        Lowest average daily emissions = top rank · Compete to live greener
      </div>
    </div>""", unsafe_allow_html=True)

    df = get_leaderboard()
    if df.empty:
        st.info("🌱 No entries yet. Be the first to log your carbon footprint!"); return

    df = df.reset_index(drop=True)
    df["rank"] = df.index + 1
    df["green_score"] = df["avg_co2"].apply(lambda x: max(0, 100 - min(100, (x/60)*100)))

    # Top 3 cards
    st.markdown('<div class="section-title">🥇 Top Eco Champions</div>', unsafe_allow_html=True)
    top_n = min(3, len(df))
    medals = ["🥇","🥈","🥉"]
    border_c = ["#d97706","#64748b","#92400e"]
    top_cols = st.columns(top_n)
    for i in range(top_n):
        row = df.iloc[i]
        rc = REGION_CONFIG.get(row["region"], REGION_CONFIG["Global Average"])
        with top_cols[i]:
            st.markdown(f"""
            <div class="eco-card" style="text-align:center;border-top:3px solid {border_c[i]};">
              <div style="font-size:2.2rem;">{medals[i]}</div>
              <div style="font-family:'Fraunces',serif;font-size:1.1rem;color:#0d3b2e;font-weight:700;margin:0.3rem 0;">
                {row['username']}
              </div>
              <div style="font-size:0.76rem;color:#7aab8a;margin-bottom:0.5rem;">{rc['flag']} {row['region']}</div>
              <div style="font-family:'Fraunces',serif;font-size:2rem;font-weight:900;color:#16a34a;line-height:1;">
                {row['avg_co2']:.1f}
              </div>
              <div style="font-size:0.76rem;color:#7aab8a;">kg CO₂/day avg</div>
              <div style="margin-top:0.4rem;font-size:0.76rem;color:#7aab8a;">
                {int(row['entries'])} entries · Best: {row['best_day']:.1f}kg
              </div>
            </div>""", unsafe_allow_html=True)

    # Full rankings
    st.markdown('<div class="section-title">📋 Full Rankings</div>', unsafe_allow_html=True)
    rank_cls = ["gold","silver","bronze"]
    badge_map = ["bg-gold","bg-silver","bg-bronze"]
    badge_lbl = ["🥇 Champion","🥈 Runner-up","🥉 Third"]
    for _, row in df.iterrows():
        rank = int(row["rank"])
        rc   = RANK_CSS = rank_cls[rank-1] if rank <= 3 else ""
        bcls = badge_map[rank-1] if rank <= 3 else "bg-green"
        blbl = badge_lbl[rank-1] if rank <= 3 else f"Rank #{rank}"
        reg  = REGION_CONFIG.get(row["region"], REGION_CONFIG["Global Average"])
        bar  = max(5, min(100, 100 - (row["avg_co2"] / 60 * 100)))
        st.markdown(f"""
        <div class="lb-row">
          <div class="lb-rank {RANK_CSS}">#{rank}</div>
          <div style="flex:1;min-width:0;">
            <div class="lb-username">{row['username']}</div>
            <div class="lb-sub">{reg['flag']} {row['region']} · {int(row['entries'])} entries · Last: {str(row.get('last_log',''))[:10]}</div>
            <div class="cbar-bg"><div class="cbar-fill" style="width:{bar}%;"></div></div>
          </div>
          <div style="text-align:right;">
            <div class="lb-co2">{row['avg_co2']:.1f} <span style="font-size:0.75rem;color:#7aab8a;">kg/day</span></div>
            <span class="lb-badge {bcls}">{blbl}</span>
          </div>
        </div>""", unsafe_allow_html=True)

    # Chart
    st.markdown('<div class="section-title">📊 Visual Comparison</div>', unsafe_allow_html=True)
    bar_colors = ["#d97706" if i==0 else "#64748b" if i==1 else "#92400e" if i==2
                  else "#22c55e" for i in range(len(df))]
    fig = go.Figure(go.Bar(x=df["username"], y=df["avg_co2"], marker_color=bar_colors,
                            text=[f"{v:.1f}" for v in df["avg_co2"]],
                            textposition="outside", textfont=dict(color="#1a7a4a", size=10)))
    fig.add_hline(y=12.9, line_dash="dot", line_color="#dc2626",
                  annotation_text="Global avg (12.9kg)", annotation_font_color="#dc2626",
                  annotation_font_size=10)
    fig.add_hline(y=5.5, line_dash="dot", line_color="#16a34a",
                  annotation_text="Sustainable target (5.5kg)", annotation_font_color="#16a34a",
                  annotation_font_size=10)
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=0,r=0,t=10,b=0), height=300,
                      xaxis=dict(color="#7aab8a"), yaxis=dict(showgrid=True, gridcolor="#e2f0e8",
                      title="Avg kg CO₂/day", color="#7aab8a"),
                      font=dict(family="Cabinet Grotesk"))
    st.plotly_chart(fig, use_container_width=True)

# ─── PAGE: Impact Report ─────────────────────────────────────────────────────
def page_impact_report():
    if not st.session_state.get("logged_in"):
        st.warning("Please log in."); return

    uid    = st.session_state.user_id
    region = st.session_state.get("region", "India")
    cfg    = REGION_CONFIG[region]
    df     = get_logs(uid)

    st.markdown(f"""
    <div class="hero-banner" style="padding:1.8rem 2.5rem;">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.8rem;">
        <div>
          <div class="hero-title" style="font-size:1.55rem;">📋 Impact Report</div>
          <div style="color:rgba(255,255,255,0.65);font-size:0.82rem;">Deep-dive analysis of your environmental footprint</div>
        </div>
        <div class="region-badge">{cfg['flag']} {region}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    if df.empty:
        st.info("🌱 No data yet. Log your first entry in the Carbon Calculator."); return

    df["log_date"] = pd.to_datetime(df["log_date"])
    df_s = df.sort_values("log_date")

    # Monthly breakdown
    df_s["month"] = df_s["log_date"].dt.strftime("%b %Y")
    monthly = df_s.groupby("month")["total_co2"].mean().reset_index()

    c1, c2, c3 = st.columns(3)
    with c1:
        fig = px.bar(monthly, x="month", y="total_co2",
                     color_discrete_sequence=["#22c55e"], labels={"month":"Month","total_co2":"Avg kg CO₂"})
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          margin=dict(l=0,r=0,t=24,b=0), height=240,
                          title=dict(text="Monthly Avg CO₂", font=dict(color="#0d3b2e",size=12)),
                          xaxis=dict(color="#7aab8a"), yaxis=dict(showgrid=True,gridcolor="#e2f0e8",color="#7aab8a"),
                          font=dict(family="Cabinet Grotesk"))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        src_cols = {"Travel":"travel_co2","Electricity":"electricity_co2",
                    "Food":"food_co2","Lifestyle":"lifestyle_co2","Flights":"flight_co2"}
        avg_bd = {k: df[v].mean() for k,v in src_cols.items() if v in df.columns}
        fig2 = go.Figure(go.Pie(labels=list(avg_bd.keys()), values=list(avg_bd.values()), hole=0.5,
                                 marker_colors=["#22c55e","#06b6d4","#f59e0b","#a855f7","#f87171"],
                                 textfont=dict(color="#0d3b2e",size=10)))
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=0,r=0,t=24,b=0), height=240,
                           title=dict(text="Avg Emission Sources",font=dict(color="#0d3b2e",size=12)),
                           font=dict(family="Cabinet Grotesk",color="#5a7a6a"),
                           legend=dict(font=dict(size=9)))
        st.plotly_chart(fig2, use_container_width=True)

    with c3:
        df_s["rolling"] = df_s["total_co2"].rolling(7, min_periods=1).mean()
        fig3 = go.Figure(go.Scatter(x=df_s["log_date"], y=df_s["rolling"],
                                    mode="lines", line=dict(color="#d97706",width=2.5),
                                    fill="tozeroy", fillcolor="rgba(217,119,6,0.08)"))
        fig3.add_hline(y=cfg["avg_daily_co2"], line_dash="dot", line_color="#dc2626",
                       annotation_text=f"{region} avg", annotation_font_color="#dc2626",
                       annotation_font_size=10)
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           margin=dict(l=0,r=0,t=24,b=0), height=240,
                           title=dict(text="7-Day Rolling Avg", font=dict(color="#0d3b2e",size=12)),
                           xaxis=dict(showgrid=False,color="#7aab8a"),
                           yaxis=dict(showgrid=True,gridcolor="#e2f0e8",color="#7aab8a"),
                           font=dict(family="Cabinet Grotesk"))
        st.plotly_chart(fig3, use_container_width=True)

    # Benchmark
    st.markdown('<div class="section-title">🌍 How You Compare</div>', unsafe_allow_html=True)
    user_avg = df["total_co2"].mean()
    bm = {"Your Avg":user_avg, f"{region} Avg":cfg["avg_daily_co2"], "Global Avg":12.9, "1.5°C Target":5.5}
    bm_c = ["#22c55e","#06b6d4","#f59e0b","#16a34a"]
    fig_bm = go.Figure(go.Bar(x=list(bm.keys()), y=list(bm.values()), marker_color=bm_c,
                               text=[f"{v:.1f}kg" for v in bm.values()],
                               textposition="outside", textfont=dict(color="#1a7a4a",size=10)))
    fig_bm.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                         margin=dict(l=0,r=0,t=10,b=0), height=260,
                         yaxis=dict(showgrid=True,gridcolor="#e2f0e8",title="kg CO₂/day",color="#7aab8a"),
                         xaxis=dict(color="#7aab8a"), font=dict(family="Cabinet Grotesk"))
    st.plotly_chart(fig_bm, use_container_width=True)

    # Transport analysis
    if "transport_mode" in df.columns:
        st.markdown('<div class="section-title">🚗 Transport Pattern</div>', unsafe_allow_html=True)
        tc = df.groupby("transport_mode").agg(trips=("travel_km","count"),
                                               avg_km=("travel_km","mean")).reset_index()
        fig_t = px.bar(tc, x="transport_mode", y="trips", color="avg_km",
                       color_continuous_scale=["#22c55e","#f59e0b","#dc2626"],
                       labels={"transport_mode":"Mode","trips":"Days Used","avg_km":"Avg km"})
        fig_t.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            margin=dict(l=0,r=0,t=10,b=0), height=240,
                            xaxis=dict(color="#7aab8a"), yaxis=dict(showgrid=True,gridcolor="#e2f0e8",color="#7aab8a"),
                            font=dict(family="Cabinet Grotesk"),
                            coloraxis_colorbar=dict(tickfont=dict(color="#7aab8a"),
                                                    title=dict(font=dict(color="#7aab8a"))))
        st.plotly_chart(fig_t, use_container_width=True)

    # Smart Insights block
    st.markdown('<div class="section-title">💡 AI-Powered Insights</div>', unsafe_allow_html=True)
    for ins in generate_insights(df, region):
        css = f"insight-{ins['type']}"
        st.markdown(f'<div class="{css}">{ins["icon"]} {ins["text"]}</div>', unsafe_allow_html=True)

# ─── PAGE: Settings ───────────────────────────────────────────────────────────
def page_settings():
    if not st.session_state.get("logged_in"):
        st.warning("Please log in."); return

    uid = st.session_state.user_id
    s   = get_user_settings(uid)

    st.markdown("""
    <div class="hero-banner" style="padding:1.8rem 2.5rem;">
      <div class="hero-title" style="font-size:1.55rem;">⚙️ Settings & API Keys</div>
      <div style="color:rgba(255,255,255,0.65);font-size:0.82rem;">
        Add API keys to unlock AI assistant and live news features
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-title">🤖 AI Assistant</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="tip-box">
    Add either a <b>Gemini</b> or <b>OpenAI</b> key to power the AI assistant with real intelligence.
    Without a key, the built-in knowledge base is used (still useful, but less dynamic).
    <br><br>• <b>Gemini 1.5 Flash</b>: Free tier available at <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:#16a34a;">aistudio.google.com</a><br>
    • <b>OpenAI GPT-3.5</b>: Pay-per-use at <a href="https://platform.openai.com/api-keys" target="_blank" style="color:#16a34a;">platform.openai.com</a>
    </div>""", unsafe_allow_html=True)

    with st.form("settings_form"):
        gemini_key = st.text_input("🔮 Gemini API Key",
                                    value=s.get("gemini", ""),
                                    type="password",
                                    placeholder="AIzaSy...")
        openai_key = st.text_input("🤖 OpenAI API Key",
                                    value=s.get("openai", ""),
                                    type="password",
                                    placeholder="sk-...")

        st.markdown('<div class="section-title">📰 News Feed</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="tip-box">
        Optional: Add a NewsAPI key for additional news sources (Reuters, AP, CNN).
        Free tier at <a href="https://newsapi.org/register" target="_blank" style="color:#16a34a;">newsapi.org</a>.
        Without it, RSS feeds from BBC/Guardian/NYT are used automatically (no key needed).
        </div>""", unsafe_allow_html=True)
        newsapi_key = st.text_input("📰 NewsAPI Key",
                                     value=s.get("newsapi", ""),
                                     type="password",
                                     placeholder="abc123...")

        st.markdown('<div class="section-title">🌍 Region</div>', unsafe_allow_html=True)
        cur_region = st.session_state.get("region", "India")
        new_region = st.selectbox("Default Region", list(REGION_CONFIG.keys()),
                                   index=list(REGION_CONFIG.keys()).index(cur_region))

        if st.form_submit_button("💾 Save Settings", use_container_width=True):
            save_user_settings(uid, gemini_key, newsapi_key, openai_key)
            if new_region != cur_region:
                # Update user region
                conn = get_conn()
                conn.execute("UPDATE users SET region=? WHERE id=?", (new_region, uid))
                conn.commit(); conn.close()
                st.session_state.region = new_region
            st.success("✅ Settings saved!")
            st.rerun()

    st.markdown('<div class="section-title">📊 Data Management</div>', unsafe_allow_html=True)
    df = get_logs(uid)
    st.info(f"You have **{len(df)} entries** in your carbon log.")
    if st.button("📥 Export My Data (CSV)"):
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", csv, file_name="ecotrack_my_data.csv", mime="text/csv")

# ─── Sidebar ───────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:1.2rem 0 0.8rem;">
          <div style="font-size:1.9rem;">🌿</div>
          <div style="font-family:'Fraunces',serif;font-size:1.25rem;color:#e8f5e0;font-weight:900;">EcoTrack</div>
          <div style="font-size:0.65rem;color:rgba(168,216,184,0.5);letter-spacing:0.1em;text-transform:uppercase;">
            v3.0 · AI-Powered
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<hr style="border-color:rgba(168,216,184,0.15);margin:0.3rem 0;">', unsafe_allow_html=True)

        if st.session_state.get("logged_in"):
            region = st.session_state.get("region", "India")
            rc = REGION_CONFIG[region]
            gami = compute_gamification(get_logs(st.session_state.user_id))
            st.markdown(f"""
            <div style="text-align:center;padding:0.5rem 0 0.7rem;">
              <div style="font-size:1.1rem;">{rc['flag']}</div>
              <div style="color:#e8f5e0;font-weight:700;font-size:0.88rem;">{st.session_state.username}</div>
              <div style="color:rgba(168,216,184,0.6);font-size:0.72rem;">{region}</div>
              <div style="color:#a8d8b8;font-size:0.75rem;margin-top:0.2rem;">
                {gami['level']} · 🔥{gami['streak']}d · ⭐{gami['points']}pts
              </div>
            </div>""", unsafe_allow_html=True)

        pages_pub  = ["Home", "Leaderboard", "Climate News"]
        pages_priv = ["Dashboard", "Carbon Calculator", "Impact Report",
                      "AI Assistant", "Settings"]
        icons = {"Home":"🏠","Leaderboard":"🏆","Climate News":"🌐",
                 "Dashboard":"📊","Carbon Calculator":"🧮",
                 "Impact Report":"📋","AI Assistant":"🤖","Settings":"⚙️",
                 "Signup":"📝","Login":"🔑"}

        if not st.session_state.get("logged_in"):
            pages_pub += ["Signup", "Login"]

        pages = pages_pub + (pages_priv if st.session_state.get("logged_in") else [])
        current = st.session_state.get("page", "Home")

        for pg in pages:
            active = current == pg
            lbl = f"{'▸ ' if active else ''}{icons.get(pg,'')}  {pg}"
            if st.button(lbl, key=f"nav_{pg}", use_container_width=True):
                st.session_state.page = pg; st.rerun()

        if st.session_state.get("logged_in"):
            st.markdown('<hr style="border-color:rgba(168,216,184,0.15);margin:0.5rem 0;">', unsafe_allow_html=True)
            if st.button("🚪 Logout", use_container_width=True):
                for k in ["logged_in","user_id","username","region","chat_history","calc_result"]:
                    st.session_state.pop(k, None)
                st.session_state.page = "Home"; st.rerun()

        st.markdown("""
        <div style="position:absolute;bottom:1rem;left:0;right:0;text-align:center;
                    font-size:0.6rem;color:rgba(168,216,184,0.25);">
          EcoTrack v3.0 · Built for Earth 🌍
        </div>""", unsafe_allow_html=True)

# ─── Main ──────────────────────────────────────────────────────────────────────
def main():
    init_db()
    inject_css()

    if "page" not in st.session_state:
        st.session_state.page = "Home"

    render_sidebar()

    routing = {
        "Home":             page_home,
        "Signup":           page_signup,
        "Login":            page_login,
        "Dashboard":        page_dashboard,
        "Carbon Calculator":page_calculator,
        "Impact Report":    page_impact_report,
        "Leaderboard":      page_leaderboard,
        "Climate News":     page_news,
        "AI Assistant":     page_ai_assistant,
        "Settings":         page_settings,
    }
    routing.get(st.session_state.get("page", "Home"), page_home)()

if __name__ == "__main__":
    main()
