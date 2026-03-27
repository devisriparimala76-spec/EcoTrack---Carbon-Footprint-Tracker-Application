# 🌿 EcoTrack v3.0 — Intelligent Carbon Footprint Tracker

| Feature | Details |
|---|---|
| 🌍 **Region-Aware Calc** | India, USA, UK, Germany, Australia + Global Average |
| 🔬 **6-Category Engine** | Transport, Electricity, Food, Lifestyle, Flights + source multipliers |
| 🤖 **AI Assistant** | Gemini 1.5 Flash / GPT-3.5 / Built-in KB fallback |
| 💬 **Conv. Memory** | AI chat history stored in DB, used as context |
| 📊 **User Context** | AI knows your avg CO₂, region, diet, transport mode |
| 🌐 **News Feed** | BBC, Guardian, NYT via RSS (no key needed) + NewsAPI optional |
| 🔥 **Streak Tracking** | Consecutive daily logging streaks |
| 🏅 **8 Badges** | Beginner → Climate Hero with unlock conditions |
| ⭐ **Points System** | Entries × 10 + streak × 25 + carbon reduction bonus |
| 💡 **Smart Insights** | 6 auto-generated insights: week-over-week, best/worst, patterns |
| 📈 **7-Day Rolling Avg** | Trend line on dashboard + weekly bar chart |
| 🏆 **Leaderboard** | All users ranked by avg emissions with bar chart |
| 📅 **Date-wise Logs** | Log any past date, full history view |
| ⚙️ **Settings Page** | API key management + region + CSV export |
| 📱 **Mobile-Responsive** | CSS media queries, flexible grid, compact mode |

## 🧪 Carbon Emission Factors

### Transport (kg CO₂/km)
| Mode | India | USA | UK |
|---|---|---|---|
| Car (Petrol) | 0.210 | 0.267 | 0.170 |
| Car (EV) | 0.148 | 0.081 | 0.040 |
| Bus | 0.089 | 0.089 | 0.079 |
| Train | 0.041 | 0.028 | 0.035 |
| Motorcycle | 0.113 | 0.103 | 0.095 |

### Electricity (kg CO₂/kWh)
| Region | Factor | Source |
|---|---|---|
| India | 0.82 | CEA 2022 |
| USA | 0.386 | EPA 2022 |
| UK | 0.233 | BEIS 2022 |
| Germany | 0.366 | UBA 2022 |
| Australia | 0.79 | DCCEW 2022 |

### Food (kg CO₂/day)
| Diet | Factor |
|---|---|
| Vegan | 1.5 |
| Vegetarian | 2.5 |
| Flexitarian | 4.5 |
| Regular | 7.0 |
| Heavy Meat | 10.5 |

## 🏗️ Architecture

```
app.py (single file, ~900 lines)
├── Constants (REGION_CONFIG, FOOD_EMISSIONS, BADGES)
├── Database Layer (SQLite, auto-migration)
├── Calculation Engine (6-category, region-aware)
├── Gamification Engine (streaks, badges, points, levels)
├── Smart Insights Engine (pattern detection, comparisons)
├── AI Layer (Gemini → OpenAI → Built-in KB fallback)
├── News Feed (RSS + NewsAPI with 30-min cache)
├── CSS Styling (light theme, responsive, custom fonts)
└── Pages (Home, Auth, Dashboard, Calculator, AI, News, Leaderboard, Report, Settings)
```

## 📦 Dependencies
Only 3 packages needed (all standard):
- `streamlit` — UI framework
- `plotly` — interactive charts
- `pandas` — data processing

