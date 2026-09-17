from pathlib import Path


def test_alpha_contract() -> None:
    assert 'return "alpha-ready"' in Path("src/capability_alpha.py").read_text()
