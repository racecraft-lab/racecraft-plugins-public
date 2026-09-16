from pathlib import Path


def test_beta_contract() -> None:
    assert 'return "beta-ready"' in Path("src/capability_beta.py").read_text()
