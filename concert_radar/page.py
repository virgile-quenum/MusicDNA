"""
concert_radar/page.py — Streamlit page for "Concert Radar".
Wired into app.py's nav exactly like every other page module (see
app.py's `elif "..." in page: import X; X.render(...)` block).
"""

import streamlit as st
import pandas as pd

from concert_radar import pipeline as pipeline_mod
from concert_radar import export as export_mod
from concert_radar.sources import bandsintown, songkick

VIOLET       = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"
AMBER        = "#f59e0b"
RED          = "#f87171"


def _kpi(label, value):
    st.markdown(
        "<div class='metric-card'><div class='metric-val'>" + str(value) +
        "</div><div class='metric-lbl'>" + label + "</div></div>",
        unsafe_allow_html=True,
    )


def _status_pill(status):
    color = {"available": "#1DB954", "sold out": RED}.get(status, "#888")
    return ("<span style='color:" + color + ";font-size:.75em;font-weight:700;'>"
            + status + "</span>")


def _events_table(df, key_prefix, extra_col=None):
    if df.empty:
        st.info("No events matched yet in this list.")
        return None

    display = df.copy()
    display.insert(0, "Select", False)
    column_order = ["Select", "date", "artist", "venue", "city", "price",
                    "status", "my_hours"]
    if extra_col and extra_col in display.columns:
        column_order.append(extra_col)
    column_order = [c for c in column_order if c in display.columns]

    edited = st.data_editor(
        display[column_order + ["ticket_url", "sources"]],
        column_config={
            "Select": st.column_config.CheckboxColumn(required=False),
            "ticket_url": st.column_config.LinkColumn("Tickets"),
            "date": "Date", "artist": "Artist", "venue": "Venue", "city": "City",
            "price": "Price", "status": "Status", "my_hours": "My hours",
            "sources": "Sources",
        },
        hide_index=True, use_container_width=True, key=key_prefix + "_editor",
    )
    return edited


def render(dfm=None):
    st.title("Concert Radar")
    st.markdown("*Upcoming shows matched to what you actually listen to — not what's trending.*")

    if dfm is None or dfm.empty:
        st.warning("Upload your Extended History zip to enable Concert Radar.")
        return

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        region_name = st.text_input("City or region", value="Île-de-France",
                                     key="cr_region",
                                     help="Matched against the commune/postcode list in "
                                          "concert_radar/region_communes.yaml.")
    with col2:
        months_ahead = st.slider("Months ahead", 1, 6, 4, key="cr_months")
    with col3:
        run = st.button("Search concerts", type="primary", use_container_width=True)

    missing_keys = []
    if not bandsintown._app_id():
        missing_keys.append("BANDSINTOWN_APP_ID")
    if missing_keys:
        st.warning("Missing env var(s): " + ", ".join(missing_keys) +
                   ". Bandsintown results will be empty until this is set on Railway.")

    cache_key = "cr_result"
    if run:
        with st.spinner("Building your listener profile, finding similar artists, "
                        "and checking concert sources..."):
            st.session_state[cache_key] = pipeline_mod.run_pipeline(
                dfm, region_name=region_name, months_ahead=months_ahead,
            )

    result = st.session_state.get(cache_key)
    if result is None:
        st.info("Set your region and click **Search concerts**. First run can take a "
                "minute or two — every source, artist and similar-artist lookup is "
                "cached afterwards.")
        return

    kpis = result["kpis"]
    c1, c2, c3, c4 = st.columns(4)
    with c1: _kpi("Events collected", kpis["events_collected"])
    with c2: _kpi("Sources used", ", ".join(kpis["sources_used"]) or "none")
    with c3: _kpi("Sources failed", len(kpis["sources_failed"]))
    with c4: _kpi("My artists matched", kpis["matches_per_tab"]["my_artists"])

    if kpis["sources_failed"]:
        with st.expander("Source failures (click to see why)"):
            for f in kpis["sources_failed"]:
                st.markdown("**" + f["source"] + "**: " + "; ".join(str(e) for e in f["errors"]))

    tab1, tab2, tab3, tab4 = st.tabs(
        ["My artists", "Close to my taste", "To verify", "Small venues & festivals"]
    )

    with tab1:
        st.caption("Sorted by how much you actually listen to the artist — not by date.")
        edited_my = _events_table(result["my_artists"], "my")

    with tab2:
        st.caption("Artists similar to your top 30, matched via Last.fm — not already in your library.")
        edited_close = _events_table(result["close_to_taste"], "close", extra_col="close_to")

    with tab3:
        st.caption("Flagged for a reason — homonym risk, tribute act, agency-as-venue, "
                   "single unconfirmed source, or an artist you barely listen to.")
        edited_verify = _events_table(result["to_verify"], "verify", extra_col="reason")

    with tab4:
        st.info("V2 — not built yet. Will score unmatched small-venue and festival "
               "listings by genre-tag overlap with your top genres, with a bonus for "
               "sub-€20 tickets and town-run venues. See concert_radar/sources/README "
               "TODOs for the planned adapters (New Morning, La Cigale, Villes des "
               "Musiques du Monde, Africolor, etc.).")

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        xlsx_bytes = export_mod.build_xlsx(
            result["my_artists"], result["close_to_taste"], result["to_verify"]
        )
        st.download_button("Download .xlsx (all tabs)", data=xlsx_bytes,
                           file_name="concert_radar.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with col_b:
        selected_events = []
        for edited in (edited_my, edited_close, edited_verify):
            if edited is not None and "Select" in edited.columns:
                selected_events += edited[edited["Select"]].to_dict("records")
        if selected_events:
            ics_bytes = export_mod.build_ics(selected_events)
            st.download_button("Download .ics for %d selected event(s)" % len(selected_events),
                               data=ics_bytes, file_name="concert_radar.ics",
                               mime="text/calendar")
        else:
            st.caption("Tick \"Select\" on events above to export a .ics for them.")
