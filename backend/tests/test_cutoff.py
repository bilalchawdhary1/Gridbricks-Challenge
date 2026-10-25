from datetime import date
from app.services.cutoff import decision_cutoff


def test_january_cutoff_is_utc_equal():
    c = decision_cutoff(date(2026, 1, 15))
    assert c.isoformat() == "2026-01-14T09:00:00+00:00"


def test_summer_cutoff_converts_bst_to_utc():
    c = decision_cutoff(date(2026, 7, 15))
    assert c.isoformat() == "2026-07-14T08:00:00+00:00"