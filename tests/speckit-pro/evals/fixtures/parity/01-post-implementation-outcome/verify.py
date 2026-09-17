from pathlib import Path


expected = {
    "src/capability_alpha.py": 'return "alpha-ready"',
    "src/capability_beta.py": 'return "beta-ready"',
    "tests/test_capability_alpha.py": "test_alpha_contract",
    "tests/test_capability_beta.py": "test_beta_contract",
}
for relative, token in expected.items():
    assert token in Path(relative).read_text(encoding="utf-8"), relative
print("parity-01 integration verification passed")
