"""tests/concert_radar/test_region.py"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from concert_radar import region as region_mod


def test_postcode_in_idf():
    assert region_mod.postcode_in_region("75011")
    assert region_mod.postcode_in_region("93200")
    assert not region_mod.postcode_in_region("13001")  # Marseille


def test_city_in_idf_communes():
    communes = region_mod.load_region_communes()
    assert region_mod.event_in_region("Saint-Denis", "", communes)
    assert region_mod.event_in_region("paris", "", communes)  # case-insensitive


def test_city_outside_region():
    communes = region_mod.load_region_communes()
    assert not region_mod.event_in_region("Marseille", "13001", communes)


def test_no_city_no_postcode_not_in_region():
    communes = region_mod.load_region_communes()
    assert not region_mod.event_in_region("", "", communes)
