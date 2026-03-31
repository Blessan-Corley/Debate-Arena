import importlib


def test_con_agent_module_is_importable_from_expected_path():
    module = importlib.import_module("agents.con_agent")

    assert hasattr(module, "ConAgent")
