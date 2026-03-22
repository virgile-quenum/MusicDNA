import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter

VIOLET       = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"
GREEN        = "#1DB954"
AMBER        = "#f59e0b"
RED          = "#f87171"

# ── Category detection ────────────────────────────────────────────────────────

CATEGORIES = {
    "Sport": [
        "sport", "football", "rugby", "tennis", "nba", "nfl", "ufc", "mma",
        "cycling", "velo", "foot", "ligue 1", "premier league", "champions league",
        "formule 1", "f1", "marathon", "running", "fitness", "gym", "workout",
        "transfert", "mercato", "inside the nba", "all access", "the athletic",
        "tifo", "extended highlights", "offside", "tackle", "goal", "score",
        "basketball", "baseball", "hockey", "golf", "ski", "natation", "boxe",
        "wrestling", "ligament", "blessure", "injury"
    ],
    "Finance / Investing": [
        "invest", "finance", "bourse", "trading", "crypto", "bitcoin", "ethereum",
        "startup", "vc", "venture", "business", "entrepreneurship", "entrepreneur",
        "money", "argent", "patrimoine", "immobilier", "real estate", "stock",
        "market", "economic", "economie", "richesse", "millionaire", "billionaire",
        "warren buffet", "elon", "wall street", "bloomberg", "the economist",
        "planet money", "how i built", "masters of scale", "acquired", "all-in",
        "lex fridman", "tim ferriss", "y combinator", "sequoia"
    ],
    "True Crime": [
        "crime", "murder", "killer", "detective", "cold case", "unsolved",
        "criminal", "meurtre", "enquete", "affaire", "justice", "prison",
        "serial", "forensic", "investigation", "fbi", "cia", "espionnage",
        "corruption", "scandale", "true crime", "my favorite murder",
        "sword and scale", "casefile", "generation why", "audiochuck"
    ],
    "Tech / AI": [
        "tech", "technologie", "ai", "intelligence artificielle", "startup",
        "silicon valley", "code", "developer", "data", "algorithm", "machine learning",
        "chatgpt", "openai", "google", "apple", "amazon", "meta", "microsoft",
        "wired", "lex fridman", "hard fork", "acquired", "big technology",
        "darknet diaries", "risky business", "syntax", "javascript"
    ],
    "Culture / Society": [
        "culture", "société", "politique", "politique", "news", "actualité",
        "histoire", "history", "art", "cinema", "film", "musique", "music",
        "livre", "book", "litterature", "philosophy", "philosophie",
        "npr", "radiolab", "this american life", "serial", "snap judgment",
        "99 invisible", "freakonomics", "hidden brain", "stuff you missed"
    ],
    "Well-being / Self-help": [
        "meditation", "mindfulness", "yoga", "mental health", "santé mentale",
        "therapie", "therapy", "psychologie", "psychology", "bonheur", "happiness",
        "développement personnel", "self help", "motivation", "coaching",
        "huberman", "andrew huberman", "tim ferriss", "tony robbins",
        "feel better live more", "on purpose", "diary of a ceo"
    ],
    "Comedy": [
        "comedy", "humour", "humor", "funny", "laugh", "joke", "stand up",
        "conan", "joe rogan", "my brother my brother", "comedy bang bang",
        "how did this get made", "bad friends", "armchair expert",
        "call her daddy", "normal gossip", "rire", "sketch"
    ],
}

LANGUAGE_SIGNALS = {
    "French": [
        "france", "français", "francais", "le monde", "liberation", "figaro",
        "rfi", "france inter", "france culture", "bfm", "europe 1", "rtl",
        "afrique", "québec", "belgique", "suisse romande", "arte"
    ],
    "English": [
        "the daily", "new york times", "bbc", "guardian", "npr", "abc",
        "cnn", "fox", "msnbc", "bloomberg", "wsj", "economist", "atlantic",
        "washington post", "new yorker"
    ],
}

VERDICTS = {
    "Sport": [
        "You consume {sport_h:.0f}h of sport content per year. That's the career you never had, processed vicariously through other people's ligaments.",
        "Sport is {sport_pct:.0f}% of your podcast diet. The athletic performance you couldn't deliver, you analyze instead. Respect.",
        "{sport_h:.0f} hours of sport podcasts. You know every tactical system. You have never run a 5k in your life.",
    ],
    "Finance / Investing": [
        "Finance podcasts: {finance_h:.0f}h. You are one more episode away from quitting your job to trade full-time. You are not.",
        "{finance_pct:.0f}% of your listening is finance content. The next Warren Buffet. Or at least that is what you tell yourself at 7am.",
        "{finance_h:.0f}h of investing content. Your portfolio would suggest you have learned very little. But the conviction is real.",
    ],
    "True Crime": [
        "True crime at {crime_h:.0f}h. You have solved more cases in your head than the actual police. You are wrong about all of them.",
        "{crime_pct:.0f}% true crime. You are now incapable of meeting a stranger without quietly assessing if they could be a suspect.",
        "{crime_h:.0f}h of murder and investigation content. Your friends think you are morbid. They are correct.",
    ],
    "Tech / AI": [
        "{tech_h:.0f}h of tech and AI content. You have been saying 'this changes everything' every 6 months since 2012. Something will eventually change.",
        "Tech podcasts at {tech_pct:.0f}%. You have strong opinions about which AI will win. Nobody has asked.",
        "{tech_h:.0f}h. You know more about Sam Altman's daily routine than your own. This is a problem.",
    ],
    "Well-being / Self-help": [
        "{wellbeing_h:.0f}h of self-help content. You are optimising yourself into a version nobody actually knows how to talk to.",
        "Well-being at {wellbeing_pct:.0f}% of your listening. The irony of stress-listening to relaxation content has not escaped us.",
        "{wellbeing_h:.0f}h. You have more morning routines than you have mornings. Pick one.",
    ],
    "Comedy": [
        "{comedy_h:.0f}h of comedy. You laugh alone in public transport. People move away. You do not care.",
        "Comedy at {comedy_pct:.0f}%. The only healthy content in this list. You are welcome.",
        "{comedy_h:.0f}h of comedy podcasts. You quote episodes at people who have not listened to them. They smile politely. They do not find it funny.",
    ],
    "Culture / Society": [
        "{culture_h:.0f}h of culture and society. You have opinions about things that have not happened yet. You call it being informed.",
        "Culture at {culture_pct:.0f}%. You are the person who starts sentences with 'I heard a podcast about this...'",
        "{culture_h:.0f}h. You have enough context on everything to be mildly insufferable at dinner parties.",
    ],
}

def _detect_category(show_name, episode_name=""):
    text = (show_name + " " + episode_name).lower()
    scores = {}
    for cat, keywords in CATEGORIES.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[cat] = score
    return max(scores, key=scores.get) if scores else "Other"

def _detect_language(show_name):
    text = show_name.lower()
    for lang, signals in LANGUAGE_SIGNALS.items():
        if any(s in text for s in signals):
            return lang
    return "Unknown"

def _card(content, border=VIOLET):
    st.markdown(
        "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
        "border-left:3px solid " + border + ";border-radius:8px;"
        "padding:14px;margin-bottom:10px;'>" + content + "</div>",
        unsafe_allow_html=True
    )

def render(dfp):
    st.title("Podcast Autopsy")
    st.markdown("*What you actually listen to when you are not listening to music.*")

    if dfp is None or dfp.empty:
        st.info(
            "No podcast data found. Podcasts are included in your Extended History export. "
            "Make sure you uploaded the extended zip."
        )
        return

    # enrich with category and language
    dfp = dfp.copy()
    dfp["category"] = dfp.apply(
        lambda r: _detect_category(r.get("show", ""), r.get("episode", "")), axis=1
    )
    dfp["language"] = dfp["show"].apply(_detect_language)

    total_h    = round(dfp["ms"].sum() / 3600000, 1)
    total_eps  = len(dfp)
    n_shows    = dfp["show"].nunique()
    n_episodes = dfp["episode"].nunique()
    cutoff_1y  = dfp["ts"].max() - pd.DateOffset(years=1)

    # ── Hero ─────────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    for col, val, lbl, color in [
        (c1, str(total_h) + "h",  "Total podcast time",    VIOLET_LIGHT),
        (c2, str(n_shows),         "Shows listened to",     VIOLET_LIGHT),
        (c3, str(n_episodes),      "Unique episodes",       VIOLET_LIGHT),
        (c4, str(total_eps),       "Total plays",           VIOLET_LIGHT),
    ]:
        with col:
            st.markdown(
                "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                "border-radius:10px;padding:14px;text-align:center;'>"
                "<div style='font-size:1.6em;font-weight:900;color:" + color + ";'>"
                + val + "</div>"
                "<div style='font-size:.72em;color:#555;margin-top:4px;'>" + lbl + "</div>"
                "</div>",
                unsafe_allow_html=True
            )

    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Top Shows", "Podcast Personality", "Listening Patterns", "Abandoned", "Timeline"
    ])

    # ── Tab 1: Top Shows ──────────────────────────────────────────────────────
    with tab1:
        st.markdown("### Your most-listened shows")
        show_stats = dfp.groupby("show").agg(
            hours=("ms", lambda x: round(x.sum()/3600000, 1)),
            episodes=("episode", "nunique"),
            last=("ts", "max"),
            category=("category", lambda x: x.mode()[0] if not x.empty else "Other"),
        ).sort_values("hours", ascending=False).head(20).reset_index()

        fig = go.Figure(go.Bar(
            x=show_stats["hours"],
            y=show_stats["show"],
            orientation="h",
            marker_color=VIOLET,
            text=[str(h) + "h" for h in show_stats["hours"]],
            textposition="outside",
        ))
        fig.update_layout(
            plot_bgcolor="#111", paper_bgcolor="#111", font_color="#aaa",
            yaxis=dict(autorange="reversed", tickfont=dict(size=11, color="#ccc")),
            xaxis=dict(gridcolor="#1a1a1a", title="Hours"),
            margin=dict(l=200, r=80, t=10, b=20),
            height=max(400, len(show_stats) * 28)
        )
        st.plotly_chart(fig, use_container_width=True)

        cols = st.columns(2)
        for i, (_, row) in enumerate(show_stats.iterrows()):
            last   = row["last"].strftime("%b %Y")
            silent = row["last"] < cutoff_1y
            border = RED if silent else GREEN
            with cols[i % 2]:
                _card(
                    "<div style='font-weight:700;color:#fff;font-size:.9em;'>"
                    + str(row["show"]) + "</div>"
                    "<div style='display:flex;gap:10px;margin-top:6px;flex-wrap:wrap;'>"
                    "<span style='color:#A78BFA;font-weight:700;font-size:.78em;'>"
                    + str(row["hours"]) + "h</span>"
                    "<span style='color:#555;font-size:.78em;'>"
                    + str(int(row["episodes"])) + " eps</span>"
                    "<span style='color:#555;font-size:.78em;'>"
                    + str(row["category"]) + "</span>"
                    "<span style='color:#444;font-size:.78em;'>last: " + last + "</span>"
                    + ("<span style='color:#f87171;font-size:.75em;'>silent 12m+</span>" if silent else "") +
                    "</div>",
                    border=border
                )

    # ── Tab 2: Podcast Personality ────────────────────────────────────────────
    with tab2:
        st.markdown("### What your podcasts say about you")
        st.caption("Detected from show and episode names. Brutally honest.")

        cat_hours = dfp.groupby("category")["ms"].sum().sort_values(ascending=False)
        cat_hours_h = (cat_hours / 3600000).round(1)
        total_cat_h = cat_hours_h.sum()

        # pie chart
        if not cat_hours_h.empty:
            colors = ["#7C3AED","#A78BFA","#1DB954","#f59e0b","#f87171","#60a5fa","#34d399","#555"]
            fig_pie = go.Figure(go.Pie(
                labels=cat_hours_h.index.tolist(),
                values=cat_hours_h.values.tolist(),
                marker_colors=colors[:len(cat_hours_h)],
                hole=0.4,
                textinfo="label+percent",
                textfont=dict(color="#ccc", size=12),
            ))
            fig_pie.update_layout(
                paper_bgcolor="#111", plot_bgcolor="#111",
                font=dict(color="#888"),
                legend=dict(bgcolor="#0f0f0f"),
                margin=dict(l=0, r=0, t=20, b=0),
                height=320,
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # language breakdown
        lang_counts = dfp.groupby("language")["ms"].sum().sort_values(ascending=False)
        lang_h = (lang_counts / 3600000).round(1)
        if not lang_h.empty:
            lang_items = " ".join([
                "<span style='color:#A78BFA;font-size:.82em;font-weight:700;"
                "background:#7C3AED22;padding:3px 10px;border-radius:10px;margin-right:6px;'>"
                + lang + ": " + str(h) + "h</span>"
                for lang, h in lang_h.items() if lang != "Unknown"
            ])
            if lang_items:
                st.markdown(
                    "<div style='margin-bottom:16px;'>"
                    "<span style='color:#555;font-size:.8em;'>Languages detected: </span>"
                    + lang_items + "</div>",
                    unsafe_allow_html=True
                )

        # sarcastic verdicts
        st.markdown("---")
        st.markdown(
            "<div style='color:#A78BFA;font-size:.75em;font-weight:700;"
            "text-transform:uppercase;letter-spacing:.1em;margin-bottom:12px;'>"
            "The verdict</div>",
            unsafe_allow_html=True
        )

        stats = {}
        for cat, h in cat_hours_h.items():
            key = cat.lower().replace(" / ", "_").replace(" ", "_")
            stats[key + "_h"]   = float(h)
            stats[key + "_pct"] = round(float(h) / total_cat_h * 100) if total_cat_h > 0 else 0

        # map category names to stats keys
        cat_key_map = {
            "Sport":               "sport",
            "Finance / Investing": "finance",
            "True Crime":          "crime",
            "Tech / AI":           "tech",
            "Well-being / Self-help": "wellbeing",
            "Comedy":              "comedy",
            "Culture / Society":   "culture",
        }

        shown = 0
        for cat in cat_hours_h.index[:4]:
            if cat not in VERDICTS:
                continue
            key = cat_key_map.get(cat, cat.lower())
            templates = VERDICTS[cat]
            template  = templates[shown % len(templates)]
            try:
                verdict = template.format(**stats)
            except:
                verdict = template
            color = ["#f87171", AMBER, VIOLET_LIGHT, GREEN][shown % 4]
            _card(
                "<div style='color:#ccc;font-size:.88em;line-height:1.6;'>"
                + verdict + "</div>",
                border=color
            )
            shown += 1

        if shown == 0:
            _card(
                "<div style='color:#ccc;font-size:.88em;'>"
                "Your podcast categories are undetectable. Either you listen to very niche content "
                "or your show names contain no recognizable keywords. Both are valid."
                "</div>"
            )

    # ── Tab 3: Listening Patterns ─────────────────────────────────────────────
    with tab3:
        st.markdown("### When do you listen to podcasts?")
        DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        c1, c2 = st.columns(2)
        with c1:
            hourly = dfp.groupby("hour")["ms"].sum().reindex(range(24), fill_value=0).reset_index()
            hourly.columns = ["hour", "ms"]
            hourly["hours"] = hourly["ms"] / 3600000
            fig2 = px.bar(hourly, x="hour", y="hours",
                          color_discrete_sequence=[VIOLET],
                          labels={"hours": "Hours", "hour": "Hour of day"})
            fig2.update_layout(
                plot_bgcolor="#111", paper_bgcolor="#111", font_color="#888",
                xaxis=dict(gridcolor="#222", tickmode="linear"),
                yaxis=dict(gridcolor="#222"),
                margin=dict(l=0, r=0, t=20, b=0), title="By hour"
            )
            st.plotly_chart(fig2, use_container_width=True)

        with c2:
            dow = dfp.groupby("dow")["ms"].sum().reindex(range(7), fill_value=0).reset_index()
            dow.columns = ["dow", "ms"]
            dow["hours"] = dow["ms"] / 3600000
            dow["day"]   = DAYS
            fig3 = px.bar(dow, x="day", y="hours",
                          color_discrete_sequence=[VIOLET_LIGHT],
                          labels={"hours": "Hours", "day": "Day"})
            fig3.update_layout(
                plot_bgcolor="#111", paper_bgcolor="#111", font_color="#888",
                xaxis=dict(gridcolor="#222"), yaxis=dict(gridcolor="#222"),
                margin=dict(l=0, r=0, t=20, b=0), title="By day"
            )
            st.plotly_chart(fig3, use_container_width=True)

        peak_h = int(dfp.groupby("hour")["ms"].sum().idxmax())
        peak_d = DAYS[int(dfp.groupby("dow")["ms"].sum().idxmax())]
        context = (
            "Commute hour." if 7 <= peak_h <= 9 or 17 <= peak_h <= 19 else
            "Late night. You are either an insomniac or an overthinker. Probably both." if peak_h >= 22 or peak_h <= 5 else
            "Lunch break." if 12 <= peak_h <= 14 else
            "Your dedicated podcast hour."
        )
        _card(
            "<div style='color:#ccc;font-size:.88em;line-height:1.6;'>"
            "Peak at <b style='color:#fff;'>" + str(peak_h).zfill(2) + "h</b>. "
            + context + " Biggest day: <b style='color:#fff;'>" + peak_d + "</b>."
            "</div>"
        )

    # ── Tab 4: Abandoned ─────────────────────────────────────────────────────
    with tab4:
        st.markdown("### Shows you sampled and dropped")
        st.caption("1-2 episodes only. The ones that did not survive the pilot.")

        show_ep = dfp.groupby("show")["episode"].nunique().reset_index()
        show_ep.columns = ["show", "unique_eps"]
        show_h  = dfp.groupby("show")["ms"].sum().reset_index()
        show_h["hours"] = (show_h["ms"] / 3600000).round(1)

        abandoned = (
            show_ep[show_ep["unique_eps"] <= 2]
            .merge(show_h[["show", "hours"]], on="show")
            .sort_values("hours", ascending=False)
        )
        if abandoned.empty:
            st.success("You commit to every show you start.")
        else:
            cols = st.columns(2)
            for i, (_, row) in enumerate(abandoned.iterrows()):
                with cols[i % 2]:
                    _card(
                        "<div style='font-weight:700;color:#666;font-size:.88em;'>"
                        + str(row["show"]) + "</div>"
                        "<div style='color:#444;font-size:.76em;margin-top:4px;'>"
                        + str(int(row["unique_eps"])) + " ep" + ("s" if row["unique_eps"] > 1 else "")
                        + " | " + str(row["hours"]) + "h"
                        "</div>",
                        border="#333"
                    )

    # ── Tab 5: Timeline ───────────────────────────────────────────────────────
    with tab5:
        st.markdown("### Podcast listening over time")
        monthly = dfp.groupby("ym")["ms"].sum().reset_index()
        monthly["hours"] = (monthly["ms"] / 3600000).round(1)
        fig4 = px.area(monthly, x="ym", y="hours",
                       color_discrete_sequence=[VIOLET],
                       labels={"hours": "Hours", "ym": "Month"})
        fig4.update_layout(
            plot_bgcolor="#111", paper_bgcolor="#111", font_color="#888",
            xaxis=dict(gridcolor="#222", tickangle=45),
            yaxis=dict(gridcolor="#222"),
            margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig4, use_container_width=True)

        st.markdown("### Top show per year")
        year_rows = []
        for yr, grp in dfp.groupby("year"):
            top_show = grp.groupby("show")["ms"].sum().idxmax()
            hours    = round(grp.groupby("show")["ms"].sum().max() / 3600000, 1)
            year_rows.append({"Year": yr, "Top show": top_show, "Hours": hours})
        yr_df = pd.DataFrame(year_rows).sort_values("Year", ascending=False)
        st.dataframe(yr_df.set_index("Year"), use_container_width=True)
