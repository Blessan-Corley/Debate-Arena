from types import SimpleNamespace

from agents.judge import _coerce_decision_payload


def test_coerce_decision_payload_prefers_parsed_dict():
    response = SimpleNamespace(
        parsed={
            "should_interrupt": True,
            "interrupt_message": "That factual claim does not hold.",
            "should_end": False,
            "reason": "incorrect fact",
        },
        text=None,
    )

    payload = _coerce_decision_payload(response)

    assert payload.should_interrupt is True
    assert payload.interrupt_message == "That factual claim does not hold."


def test_coerce_decision_payload_falls_back_to_json_text():
    response = SimpleNamespace(
        parsed=None,
        text='{"should_interrupt": false, "interrupt_message": null, "should_end": true, "reason": "enough substance"}',
    )

    payload = _coerce_decision_payload(response)

    assert payload.should_end is True
    assert payload.reason == "enough substance"


def test_coerce_decision_payload_returns_default_for_truncated_json_text():
    response = SimpleNamespace(
        parsed=None,
        text='{"should_interrupt": true, "interrupt_message": "cut off',
    )

    payload = _coerce_decision_payload(response)

    assert payload.should_interrupt is False
    assert payload.should_end is False
