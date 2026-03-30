from types import SimpleNamespace

from agents.con import _coerce_research_payload, _coerce_search_plan_response


def test_coerce_research_payload_accepts_json_text():
    payload = _coerce_research_payload(
        '{"summary":"Search found real counter-evidence.","fact_points":["Point one.","Point two."]}'
    )

    assert payload.summary == "Search found real counter-evidence."
    assert payload.fact_points == ["Point one.", "Point two."]


def test_coerce_research_payload_falls_back_for_non_json_grounded_text():
    payload = _coerce_research_payload(
        "Search suggests the case is weaker than it looks.\n"
        "- Flattening management often reduces coaching depth.\n"
        "- AI automation gains depend on clean process design.\n"
    )

    assert "case is weaker" in payload.summary
    assert payload.fact_points


def test_coerce_search_plan_response_returns_default_for_truncated_json():
    response = SimpleNamespace(
        parsed=None,
        text='{"needs_search": true, "query": "latest Amazon layoff evidence',
    )

    payload = _coerce_search_plan_response(response)

    assert payload.needs_search is False
    assert payload.query is None
