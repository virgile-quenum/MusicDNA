"""tests/concert_radar/test_profile.py"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import math
import pandas as pd
import pytest

from concert_radar import profile as profile_mod


def _mk_dfm(rows):
    """rows: list of (artist, hours_ago_days, ms) → builds a minimal dfm."""
    data = []
    now = pd.Timestamp.now()
    for artist, days_ago, ms in rows:
        data.append({
            "ts": now - pd.Timedelta(days=days_ago),
            "artistName": artist,
            "trackName": "Track",
            "albumName": "Album",
            "ms": ms,
        })
    return pd.DataFrame(data)


def test_empty_dfm_returns_empty_frame():
    result = profile_mod.build_artist_profile(pd.DataFrame(), check_life_span=False)
    assert result.empty
    assert "affinity_score" in result.columns


def test_affinity_score_formula():
    # one artist, all listening within the last 12 months → recency_weight = 1.0
    dfm = _mk_dfm([("Artist A", 10, 3_600_000 * 10)])  # 10 hours, 10 days ago
    result = profile_mod.build_artist_profile(dfm, check_life_span=False)
    row = result.iloc[0]
    expected_score = math.log1p(10) * 1.0
    assert row["affinity_score"] == pytest.approx(expected_score, rel=1e-6)


def test_old_loyalty_does_not_dominate_recent_intent():
    # Artist A: 169 hours, all listened to 3 years ago (recency_weight ~0.5)
    # Artist B: 20 hours, all within the last year (recency_weight = 1.0)
    dfm = _mk_dfm([
        ("Artist A (old loyalty)", 3 * 365, 3_600_000 * 169),
        ("Artist B (current)", 30, 3_600_000 * 20),
    ])
    result = profile_mod.build_artist_profile(dfm, check_life_span=False)
    result = result.set_index("artist")
    score_a = result.loc["Artist A (old loyalty)", "affinity_score"]
    score_b = result.loc["Artist B (current)", "affinity_score"]
    # log1p(169)*0.5 ≈ 2.567   vs   log1p(20)*1.0 ≈ 3.045
    assert score_b > score_a


def test_deceased_artist_excluded_from_eligible(monkeypatch):
    # spec trap: Terry Callier — deceased, must never appear in "My artists"
    # even with the highest hours.
    dfm = _mk_dfm([
        ("Terry Callier", 10, 3_600_000 * 500),   # huge hours
        ("Living Artist", 10, 3_600_000 * 1),
    ])

    def fake_status(artist_name, overrides):
        if artist_name == "Terry Callier":
            return "ended", "deceased"
        return "active", ""

    monkeypatch.setattr(profile_mod, "artist_status", fake_status)
    result = profile_mod.build_artist_profile(dfm, check_life_span=True)
    result = result.set_index("artist")

    assert result.loc["Terry Callier", "eligible"] == False
    assert result.loc["Living Artist", "eligible"] == True


def test_extra_kids_keywords_filtered():
    dfm = _mk_dfm([
        ("Some Baby Lullaby Artist", 5, 3_600_000 * 3),
        ("Real Artist", 5, 3_600_000 * 3),
    ])
    result = profile_mod.build_artist_profile(dfm, check_life_span=False)
    assert "Some Baby Lullaby Artist" not in result["artist"].tolist()
    assert "Real Artist" in result["artist"].tolist()


def test_eligibility_thresholds_configurable():
    dfm = _mk_dfm([("Tiny Artist", 5, 3_600_000 * 0.1)])  # 0.1h, below default min_hours
    default_result = profile_mod.build_artist_profile(dfm, check_life_span=False)
    assert default_result.iloc[0]["eligible"] == False

    lenient_result = profile_mod.build_artist_profile(dfm, min_hours=0.01, check_life_span=False)
    assert lenient_result.iloc[0]["eligible"] == True


def test_overrides_yaml_not_touring(tmp_path, monkeypatch):
    override_content = (
        '"Test Artist Override":\n'
        "  status: not_touring\n"
        '  reason: "test"\n'
    )
    override_file = tmp_path / "overrides.yaml"
    override_file.write_text(override_content, encoding="utf-8")
    monkeypatch.setattr(profile_mod, "_OVERRIDES_PATH", str(override_file))

    overrides = profile_mod.load_overrides()
    status, reason = profile_mod.artist_status("Test Artist Override", overrides)
    assert status == "not_touring"
