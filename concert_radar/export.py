"""
concert_radar/export.py — .xlsx export (3 tabs) and .ics calendar export for
selected events.
"""

import io
import uuid
from datetime import datetime, date


def build_xlsx(my_df, close_df, verify_df):
    """Returns xlsx file bytes with one sheet per tab."""
    buf = io.BytesIO()
    with __import__("pandas").ExcelWriter(buf, engine="openpyxl") as writer:
        my_df.to_excel(writer, sheet_name="My artists", index=False)
        close_df.to_excel(writer, sheet_name="Close to my taste", index=False)
        verify_df.to_excel(writer, sheet_name="To verify", index=False)
    buf.seek(0)
    return buf.getvalue()


def _ics_escape(text):
    return str(text).replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")


def _fmt_date(d):
    if isinstance(d, str):
        try:
            d = datetime.strptime(d[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    if isinstance(d, datetime):
        d = d.date()
    if isinstance(d, date):
        return d.strftime("%Y%m%d")
    return None


def build_ics(events):
    """
    events: list of dicts with date, artist, venue, city, ticket_url.
    All-day events (concert start times aren't reliably available from
    Bandsintown/Songkick listings) — the venue/city goes in the location
    field, ticket link in the description.
    """
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//MusicDNA//Concert Radar//EN"]
    for ev in events:
        day = _fmt_date(ev.get("date"))
        if not day:
            continue
        uid = str(uuid.uuid4())
        summary = _ics_escape(ev.get("artist", "Concert"))
        location = _ics_escape(", ".join(filter(None, [ev.get("venue"), ev.get("city")])))
        description = _ics_escape(ev.get("ticket_url", ""))
        lines += [
            "BEGIN:VEVENT",
            "UID:%s" % uid,
            "DTSTAMP:%sT000000Z" % datetime.utcnow().strftime("%Y%m%d"),
            "DTSTART;VALUE=DATE:%s" % day,
            "SUMMARY:%s" % summary,
            "LOCATION:%s" % location,
            "DESCRIPTION:%s" % description,
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines).encode("utf-8")
