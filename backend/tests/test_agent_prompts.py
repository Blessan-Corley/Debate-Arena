from agents.host import SYSTEM_PROMPT


def test_host_prompt_uses_gopinath_name():
    assert "GOPINATH" in SYSTEM_PROMPT
    assert "MAXWELL IRON" not in SYSTEM_PROMPT
